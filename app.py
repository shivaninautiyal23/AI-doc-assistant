from fastapi import FastAPI, UploadFile, File
import shutil
import os

from rag_service import (
    extract_text_from_pdf,
    chunk_text,
    create_embeddings,
    store_embeddings,
    reset_vectorstore  
)

from rag_pipeline import rag_answer

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


#  UPLOAD 
@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    reset_vectorstore()

    path = f"{UPLOAD_DIR}/{file.filename}"

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)


    text = extract_text_from_pdf(path)
    chunks = chunk_text(text)
    embeddings = create_embeddings(chunks)

    store_embeddings(chunks, embeddings)

    return {"message": "uploaded + old memory cleared + new file processed"}

from rag_service import reset_vectorstore

@app.post("/reset-vectorstore")
def reset_vectorstore_api():
    reset_vectorstore()
    return {"message": "vectorstore cleared successfully"}

#  CHAT 
@app.post("/chat")
def chat(query: dict):
    return rag_answer(query["question"])

