from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import shutil

from rag_service import extract_text_from_pdf, chunk_text, create_embeddings, store_embeddings
from rag_pipeline import rag_answer

app = FastAPI()

class Query(BaseModel):
    question: str

# Upload PDF
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = f"temp_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = extract_text_from_pdf(file_path)
    chunks = chunk_text(text)
    embeddings = create_embeddings(chunks)
    store_embeddings(chunks, embeddings)

    return {"message": "File uploaded and processed successfully"}

# Chat endpoint (RAG)
@app.post("/chat")
def chat(q: Query):
    return rag_answer(q.question)
