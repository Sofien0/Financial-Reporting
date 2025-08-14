import os
import faiss
import pickle
import argparse
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Paths
INDEX_PATH = Path("data/processed/topic_rag_index.faiss")
METADATA_PATH = Path("data/processed/topic_rag_metadata.pkl")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Load embedding model
def load_model():
    print("🔗 Loading embedding model:", EMBEDDING_MODEL)
    return SentenceTransformer(EMBEDDING_MODEL)

# Load FAISS index and metadata
def load_index_and_metadata():
    print("📦 Loading FAISS index and metadata...")
    index = faiss.read_index(str(INDEX_PATH))
    with open(METADATA_PATH, "rb") as f:
        metadata = pickle.load(f)
    return index, metadata

# Embed query
def embed_query(query, model):
    return model.encode([query])

# Run interactive loop
def run_interactive_search(index, metadata, model, top_k=5):
    print("\n🧠 Topic RAG Interactive Search Engine")
    print("Type your query and press Enter (or type 'exit' to quit)\n")

    while True:
        query = input("🔍 Query: ").strip()
        if query.lower() in ["exit", "quit"]:
            print("👋 Exiting.")
            break

        query_vector = embed_query(query, model)
        distances, indices = index.search(query_vector, top_k)

        print(f"\n🔎 Top {top_k} Matches:")
        for rank, idx in enumerate(indices[0]):
            row = metadata.iloc[idx]
            print(f"\n[{rank + 1}] Score: {distances[0][rank]:.4f}")
            print(f"📄 Content: {row['content'][:300]}{'...' if len(row['content']) > 300 else ''}")
            print(f"🏷️ Sector: {row['sector']} | Subsector: {row['subsector']} | Company: {row['company']} | Year: {row['year']}")
            print(f"📁 Source: {row['source_path']}")

        print("-" * 80)

# Main
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the Topic RAG FAISS index")
    parser.add_argument("--top_k", type=int, default=5, help="Number of results to return")
    args = parser.parse_args()

    model = load_model()
    index, metadata = load_index_and_metadata()
    run_interactive_search(index, metadata, model, top_k=args.top_k)
