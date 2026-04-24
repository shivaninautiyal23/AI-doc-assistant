import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader

# Load embedding model
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# Storage paths
os.makedirs("vectorstore", exist_ok=True)
INDEX_PATH = "vectorstore/index.faiss"
TEXT_PATH = "vectorstore/texts.pkl"

# Extract text
def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# Chunking
def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i+chunk_size])
    return chunks

# Embeddings
def create_embeddings(chunks):
    return embed_model.encode(chunks)

# Store in FAISS
def store_embeddings(chunks, embeddings):
    if os.path.exists(INDEX_PATH):
        index = faiss.read_index(INDEX_PATH)
        with open(TEXT_PATH, "rb") as f:
            texts = pickle.load(f)
    else:
        index = faiss.IndexFlatL2(len(embeddings[0]))
        texts = []

    index.add(embeddings)
    texts.extend(chunks)

    faiss.write_index(index, INDEX_PATH)
    with open(TEXT_PATH, "wb") as f:
        pickle.dump(texts, f)

# Retrieve top chunks
def retrieve(query, k=3):
    index = faiss.read_index(INDEX_PATH)

    with open(TEXT_PATH, "rb") as f:
        texts = pickle.load(f)

    query_vec = embed_model.encode([query])
    distances, indices = index.search(query_vec, k)

    return [texts[i] for i in indices[0] if i < len(texts)]
