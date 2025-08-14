import pandas as pd
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import pickle

CHUNK_PATH = Path("data/processed/chunked_documents.parquet")
INDEX_PATH = Path("data/processed/topic_rag_index.faiss")
METADATA_PATH = Path("data/processed/topic_rag_metadata.pkl")

def load_chunks(path: Path) -> pd.DataFrame:
    print(f"📖 Loading chunks from {path}")
    return pd.read_parquet(path)

def embed_chunks(chunks: pd.Series, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> np.ndarray:
    print(f"🔗 Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    print(f"🧠 Embedding {len(chunks)} chunks...")
    embeddings = model.encode(chunks.tolist(), show_progress_bar=True, convert_to_numpy=True)
    return embeddings

def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    dim = embeddings.shape[1]
    print(f"🛠️ Building FAISS index with dimension {dim}")
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

def save_index(index, path: Path):
    print(f"💾 Saving FAISS index to {path}")
    faiss.write_index(index, str(path))

def save_metadata(df: pd.DataFrame, path: Path):
    print(f"💾 Saving metadata (DataFrame without embeddings) to {path}")
    metadata = df.drop(columns=["embedding"], errors="ignore")
    with open(path, "wb") as f:
        pickle.dump(metadata, f)

def topic_rag_index_builder():
    df = load_chunks(CHUNK_PATH)
    embeddings = embed_chunks(df["content"])

    # Attach embeddings to DataFrame (not mandatory, but helpful)
    df["embedding"] = embeddings.tolist()

    index = build_faiss_index(embeddings)
    save_index(index, INDEX_PATH)
    save_metadata(df, METADATA_PATH)

    print("✅ Topic RAG index built and saved.")

if __name__ == "__main__":
    topic_rag_index_builder()
