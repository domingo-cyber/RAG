import os
import json
import pandas as pd
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from openai import OpenAI

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

DATA_DIR = "data"
VECTORSTORE_DIR = "d-embeddings"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(VECTORSTORE_DIR, exist_ok=True)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# OpenRouter LLM client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def scrape_and_embed(url: str):
    firecrawl = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

    try:
        result = firecrawl.scrape_url(url, formats=["markdown", "html"])
    except Exception as e:
        raise RuntimeError(f"Firecrawl error: {e}")

    product_id = url.split("/dp/")[1].split("/")[0] if "/dp/" in url else "product"
    product_text = result.markdown or result.html or ""
    if not product_text.strip():
        raise ValueError("No usable content found for embedding.")

    file_path = os.path.join(DATA_DIR, f"{product_id}.json")
    with open(file_path, "w") as f:
        json.dump({
            "url": url,
            "product_id": product_id,
            "markdown": result.markdown,
            "html": result.html
        }, f, indent=2)

    docs = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).create_documents([product_text])
    documents = [Document(page_content=doc.page_content) for doc in docs]
    db = FAISS.from_documents(documents, embeddings)
    db.save_local(VECTORSTORE_DIR)
    return product_id


def process_file_upload(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif ext == ".csv":
        df = pd.read_csv(file_path)
        text = df.to_csv(index=False)
    elif ext == ".json":
        with open(file_path, "r") as f:
            content = json.load(f)
        text = json.dumps(content, indent=2)
    else:
        raise ValueError("Unsupported file type. Please upload PDF, CSV, or JSON.")

    if not text.strip():
        raise ValueError("❌ No text could be extracted from the file.")

    docs = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).create_documents([text])
    documents = [Document(page_content=doc.page_content) for doc in docs]
    db = FAISS.from_documents(documents, embeddings)
    db.save_local(VECTORSTORE_DIR)
    return "Embedding created from uploaded file."


def load_vectorstore():
    return FAISS.load_local(VECTORSTORE_DIR, embeddings=embeddings, allow_dangerous_deserialization=True)


def answer_query(query: str, strict: bool = True):
    db = load_vectorstore()
    retriever = db.as_retriever()
    docs = retriever.get_relevant_documents(query)
    context = "\n\n".join(doc.page_content for doc in docs[:3])

    if strict:
        prompt = f"""You are a helpful assistant.

Use only the information provided in the context below to answer the question. Do not use any external knowledge or assumptions.

Give a precise and on-point answer. Do not include any source references, elaborations, or additional explanation.query can also be in different languages so process them then give the answer in same language

If the answer is not clearly found in the context, reply with:
"I am not clear about the response from the given data."".

Context:
{context}

Question: {query}

Answer:"""
    else:
        prompt = f"\n\n{context}\n\nQuestion: {query}"

    completion = client.chat.completions.create(
        model="deepseek/deepseek-chat-v3-0324:free",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        extra_headers={
            "HTTP-Referer": "http://localhost:3000",  # Optional
            "X-Title": "RAG Assistant"                 # Optional
        }
    )
    return completion.choices[0].message.content.strip()
