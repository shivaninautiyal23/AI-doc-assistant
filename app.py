from fastapi import FastAPI
from pydantic import BaseModel
from llm_service import call_llm

app = FastAPI()

class Query(BaseModel):
    question: str

@app.post("/chat")
def chat(q: Query):
    return {"answer": call_llm(q.question)}
