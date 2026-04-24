from rag_service import retrieve
from llm_service import call_llm

def rag_answer(query):
    docs = retrieve(query)

    context = "\n\n".join(docs)

    prompt = f"""
Answer using the context only.

Context:
{context}

Question:
{query}
"""

    answer = call_llm(prompt)

    return {
        "answer": answer,
        "sources": docs
    }
