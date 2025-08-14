import requests
import pickle
import faiss
import argparse
from pathlib import Path
import pandas as pd
from sentence_transformers import SentenceTransformer

# ------------------------
# CONFIG
# ------------------------
INDEX_PATH = Path("data/processed/topic_rag_index.faiss")
METADATA_PATH = Path("data/processed/topic_rag_metadata.pkl")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
OLLAMA_URL = "http://localhost:11434/api/chat"
TOP_K = 5

# ------------------------
# Load components
# ------------------------
def load_faiss_and_metadata():
    print("📦 Loading FAISS index and metadata...")
    index = faiss.read_index(str(INDEX_PATH))
    with open(METADATA_PATH, "rb") as f:
        metadata = pickle.load(f)
    return index, metadata

def load_embedding_model():
    print("🔗 Loading embedding model:", EMBED_MODEL)
    return SentenceTransformer(EMBED_MODEL)

# ------------------------
# Embed query
# ------------------------
def embed_query(model, query):
    return model.encode([query])

# ------------------------
# Query index
# ------------------------
def retrieve_top_chunks(query, model, index, metadata, top_k=TOP_K):
    query_vector = embed_query(model, query)
    distances, indices = index.search(query_vector, top_k)

    # Build DataFrame from results
    rows = [metadata.iloc[i] for i in indices[0]]

    # Deduplicate by 'content'
    seen = set()
    unique_rows = []
    for row in rows:
        if row['content'] not in seen:
            seen.add(row['content'])
            unique_rows.append(row)

    return unique_rows

# ------------------------
# Call Ollama/Mistral
# ------------------------
def call_mistral(query, context_chunks):
    # context_chunks is a list of Pandas Series rows
    context = []
    for row in context_chunks:
        content_with_meta = (
            f"Content: {row['content']}\n"
            f"Company: {row['company']}, Sector: {row['sector']}, "
            f"Year: {row['year']}, Page: {row['page']}, Source: {row['source_path']}"
        )
        context.append(content_with_meta)

    system_prompt = (
        "You are an ESG assistant. Always answer based only on the provided context. "
        "If multiple companies are mentioned, cite each one clearly. "
        "For each fact, mention the company, page number, and source_path. "
        "If context is missing, say you don’t know. "
        "If the question is outside the ESG domain or not answerable from context, reply with: "
        "'The answer is not available in the context.'"
    )

    context_text = '\n\n'.join(context)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query}"}
    ]

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "mistral",
            "messages": messages,
            "stream": False
        },
        timeout=60
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


# ------------------------
# Interactive Chat Loop
# ------------------------
print("📦 Loading FAISS index and metadata...")
INDEX, METADATA = load_faiss_and_metadata()

print("🔗 Loading embedding model:", EMBED_MODEL)
EMBED_MODEL_INSTANCE = load_embedding_model()

def interactive_rag_chat():
    print("\n💬 ESG RAG Chat Interface (powered by Mistral via Ollama)")
    print("Type your ESG question below. Type 'exit' to quit.\n")

    while True:
        query = input("🧠 You: ").strip()
        if query.lower() in {"exit", "quit"}:
            print("👋 Goodbye!")
            break

        # Reject irrelevant questions early
        if any(bad in query.lower() for bad in ["batman", "superman", "celebrity", "movie", "pizza"]):
            print("🤖 This question appears unrelated to ESG. Please ask something ESG-related.\n")
            continue

        top_chunks = retrieve_top_chunks(query, EMBED_MODEL_INSTANCE, INDEX, METADATA)
        answer = call_mistral(query, top_chunks)

        print(f"\n🤖 Answer:\n{answer}\n")
        print("-" * 80)


# ------------------------
# Entry point
# ------------------------
if __name__ == "__main__":
    interactive_rag_chat()
