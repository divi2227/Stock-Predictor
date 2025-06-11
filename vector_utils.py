import chromadb
from sentence_transformers import SentenceTransformer

# Initialize Chroma client (in-memory)
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="stock_vectors")

# Load embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")

def create_embedding_and_store(text, doc_id="doc1"):
    """
    Create embedding for a sentence and store in ChromaDB.
    """
    embedding = model.encode(text).tolist()

    collection.add(
        documents=[text],
        embeddings=[embedding],
        ids=[doc_id]
    )

    print(f"✅ Stored vector for: \"{text}\"")
