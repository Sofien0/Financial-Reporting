import faiss
import pickle
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# Paths
INDEX_PATH = Path("data/processed/topic_rag_index.faiss")
METADATA_PATH = Path("data/processed/topic_rag_metadata.pkl")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ---- Loaders ----
def load_model():
    print("🔗 Loading embedding model:", EMBEDDING_MODEL, flush=True)
    return SentenceTransformer(EMBEDDING_MODEL)

def load_index_and_metadata():
    print("📦 Loading FAISS index and metadata...", flush=True)
    index = faiss.read_index(str(INDEX_PATH))
    with open(METADATA_PATH, "rb") as f:
        metadata = pickle.load(f)
    if isinstance(metadata, list):
        metadata = pd.DataFrame(metadata)
    return index, metadata

# ---- Embedding ----
def embed_query(query, model):
    return model.encode([query])

# ---- Search & Filtering ----
def search(index, query_vec, fetch_k):
    D, I = index.search(query_vec, fetch_k)
    return D[0], I[0]

def filter_and_rank(D, I, metric="ip", min_sim=0.70, max_distance=None):
    """
    Returns a list of (idx, score) sorted descending by 'score'.
    - For 'ip' or 'cosine': 'score' is the raw FAISS score (higher is better).
    - For 'l2': 'score' is a derived similarity = 1/(1+distance) for sorting/printing.
    """
    D = np.asarray(D)
    I = np.asarray(I)

    results = []
    if metric in {"ip", "cosine"}:
        for score, idx in zip(D, I):
            if idx < 0:
                continue
            if score >= min_sim:
                results.append((int(idx), float(score)))
        # higher is better
        results.sort(key=lambda t: t[1], reverse=True)
        return results

    elif metric == "l2":
        # If user didn't set a max_distance, use a lenient heuristic (75th percentile)
        if max_distance is None and len(D) > 0:
            max_distance = float(np.percentile(D, 75))
        for dist, idx in zip(D, I):
            if idx < 0:
                continue
            if max_distance is None or dist <= max_distance:
                sim = 1.0 / (1.0 + float(dist))  # monotonic with similarity
                results.append((int(idx), sim))
        # higher is better (via derived 'sim')
        results.sort(key=lambda t: t[1], reverse=True)
        return results

    else:
        raise ValueError(f"Unsupported metric: {metric}")

# ---- UI Loop ----
def run_interactive_search(
    index,
    metadata,
    model,
    top_k=5,
    fetch_k=30,
    metric="ip",
    min_sim=0.70,
    max_distance=None,
    show_chars=300,
):
    print("\n🧠 Topic RAG Interactive Search (with thresholding)")
    print("Type your query and press Enter (or 'exit' to quit)\n")

    while True:
        query = input("🔍 Query: ").strip()
        if query.lower() in {"exit", "quit"}:
            print("👋 Exiting.")
            break
        if not query:
            continue

        qv = embed_query(query, model)
        D, I = search(index, qv, fetch_k=fetch_k)
        ranked = filter_and_rank(D, I, metric=metric, min_sim=min_sim, max_distance=max_distance)

        if not ranked:
            if metric in {"ip", "cosine"}:
                print(f"\n⚠️ No results passed min_sim={min_sim:.2f} (metric={metric}). Try lowering it or increasing --fetch_k.\n")
            else:
                md = "auto" if max_distance is None else f"{max_distance:.4f}"
                print(f"\n⚠️ No results passed max_distance={md} (metric=l2). Try raising it or increasing --fetch_k.\n")
            continue

        ranked = ranked[:top_k]
        print(f"\n🔎 Top {len(ranked)} results (after threshold):")
        for rank, (idx, score) in enumerate(ranked, start=1):
            row = metadata.iloc[idx]

            content = row.get("content", "")
            sector = row.get("sector", "?")
            subsector = row.get("subsector", "?")
            company = row.get("company", "?")
            year = row.get("year", "?")
            page = row.get("page", "?")
            source_path = row.get("source_path", "?")

            shown = content[:show_chars] + ("..." if len(content) > show_chars else "")
            score_label = "cosine/IP" if metric in {"ip", "cosine"} else "derived-from-L2"

            print(f"\n[{rank}] Score: {score:.4f} ({score_label})")
            print(f"📄 Content: {shown}")
            print(f"🏷️ Sector: {sector} | Subsector: {subsector} | Company: {company} | Year: {year}")
            print(f"📄 Page: {page}")
            print(f"📁 Source: {source_path}")
            print("-" * 80)

# ---- Main ----
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the Topic RAG FAISS index (thresholded)")
    parser.add_argument("--top_k", type=int, default=5, help="Number of results to display after filtering")
    parser.add_argument("--fetch_k", type=int, default=30, help="How many candidates to fetch from FAISS before filtering")
    parser.add_argument("--metric", choices=["ip", "cosine", "l2"], default="ip", help="Distance metric used by the FAISS index")
    parser.add_argument("--min_sim", type=float, default=0.70, help="Minimum similarity threshold (for ip/cosine)")
    parser.add_argument("--max_distance", type=float, default=None, help="Maximum L2 distance threshold (for l2)")
    parser.add_argument("--show_chars", type=int, default=300, help="How many content characters to display per hit")

    args = parser.parse_args()

    model = load_model()
    index, metadata = load_index_and_metadata()
    run_interactive_search(
        index=index,
        metadata=metadata,
        model=model,
        top_k=args.top_k,
        fetch_k=args.fetch_k,
        metric=args.metric,
        min_sim=args.min_sim,
        max_distance=args.max_distance,
        show_chars=args.show_chars,
    )
