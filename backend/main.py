from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os

from utils import scrape_and_embed, answer_query, process_file_upload

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class URLRequest(BaseModel):
    url: str

class QueryRequest(BaseModel):
    query: str


@app.post("/scrape")
def scrape_url(req: URLRequest):
    try:
        product_id = scrape_and_embed(req.url)
        return {"message": "✅ Scraping and embedding done.", "product_id": product_id}
    except Exception as e:
        return {"error": str(e)}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = os.path.join("data", file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        message = process_file_upload(file_path)
        return {"message": message}
    except Exception as e:
        return {"error": str(e)}


@app.post("/query")
def query_doc(req: QueryRequest):
    try:
        answer = answer_query(req.query)
        return {"answer": answer}
    except Exception as e:
        return {"error": str(e)}
