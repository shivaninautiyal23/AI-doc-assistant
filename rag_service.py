import os
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader

embed_model = SentenceTransformer("all-MiniLM-L6-v2")

INDEX_PATH = "vectorstore/index.faiss"
TEXT_PATH = "vectorstore/texts.pkl"

os.makedirs("vectorstore", exist_ok=True)

# ---------------- EXTRACT ----------------
def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + " "

    return text


# ---------------- CHUNK ----------------
def chunk_text(text, chunk_size=500):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


# ---------------- EMBEDDINGS ----------------
def create_embeddings(chunks):
    return embed_model.encode(chunks, convert_to_numpy=True)


# ---------------- STORE ----------------
def store_embeddings(chunks, embeddings):
    if os.path.exists(INDEX_PATH):
        index = faiss.read_index(INDEX_PATH)
        with open(TEXT_PATH, "rb") as f:
            texts = pickle.load(f)
    else:
        index = faiss.IndexFlatL2(embeddings.shape[1])
        texts = []

    index.add(np.array(embeddings))
    texts.extend(chunks)

    faiss.write_index(index, INDEX_PATH)

    with open(TEXT_PATH, "wb") as f:
        pickle.dump(texts, f)


# ---------------- RETRIEVE ----------------
def retrieve(query, k=5):
    if not os.path.exists(INDEX_PATH):
        return []

    index = faiss.read_index(INDEX_PATH)

    with open(TEXT_PATH, "rb") as f:
        texts = pickle.load(f)

    query_vec = embed_model.encode([query], convert_to_numpy=True)

    _, indices = index.search(query_vec, k)

    return [texts[i] for i in indices[0] if i < len(texts)]
