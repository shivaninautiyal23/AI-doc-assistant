from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

print("GROQ_API_KEY:", os.getenv("GROQ_API_KEY"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_llm(prompt):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
