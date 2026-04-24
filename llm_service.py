from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_llm(prompt):
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # ✅ updated working model
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Error: {str(e)}"
