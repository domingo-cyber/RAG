import os, json
from PyPDF2 import PdfReader
import pandas as pd
from utils import save_and_embed_text

DATA_DIR = "data"

def process_file(path: str, name: str):
    ext = name.split(".")[-1].lower()
    content = ""
    if ext == "pdf":
        reader = PdfReader(path)
        content = "\n".join(p.extract_text() or "" for p in reader.pages)
    elif ext == "csv":
        df = pd.read_csv(path)
        content = df.to_csv(index=False)
    elif ext == "json":
        content = json.dumps(json.load(open(path)), indent=2)
    else:
        raise ValueError("Unsupported format.")
    doc_id = name.replace(".", "_")
    with open(os.path.join(DATA_DIR, f"{doc_id}.txt"), "w") as f:
        f.write(content)
    save_and_embed_text(content, doc_id)
    return doc_id
