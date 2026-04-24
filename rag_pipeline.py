from rag_service import retrieve
from llm_service import call_llm

def rag_answer(query):
    try:
        chunks = retrieve(query)

        if not chunks:
            return {
                "answer": "No relevant data found. Upload documents first.",
                "sources": []
            }

        context = "\n\n".join(chunks)

        prompt = f"""
            You are a helpful AI assistant.

            Answer ONLY from the context below.
            If answer is not present, say "Not found in document".

            Context:
            {context}

            Question:
            {query}
            """

        answer = call_llm(prompt)

        return {
            "answer": answer,
            "sources": chunks
        }

    except Exception as e:
        return {
            "answer": f"Error: {str(e)}",
            "sources": []
        }
