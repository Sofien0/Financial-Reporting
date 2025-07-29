import re
import pandas as pd
from pathlib import Path
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer

TEXT_ROOT = Path("data/processed/parsed_text")
BENCHMARK_PATH = Path("data/processed/benchmark_long_table_cleaned.csv")
OUTPUT_PATH = Path("data/processed/generated_topics_by_subsector.csv")

def clean_text(text: str) -> str:
    lines = text.splitlines()
    lines = [line.strip() for line in lines if len(line.strip()) > 5]
    lines = [line for line in lines if not re.search(r"page \d+|esg|contents|©", line, re.IGNORECASE)]
    return " ".join(lines)

def normalize(name: str) -> str:
    return re.sub(r"[\W_]+", " ", name).strip().lower()

def load_benchmark_metadata() -> pd.DataFrame:
    df = pd.read_csv(BENCHMARK_PATH)
    df["company_clean"] = df["company"].apply(normalize)
    return df[["company_clean", "sector", "subsector"]].drop_duplicates()

def load_and_group_by_subsector(text_root: Path, metadata_df: pd.DataFrame) -> dict:
    grouped = defaultdict(list)
    matched, skipped = 0, 0

    for txt_file in text_root.glob("*.txt"):
        text = txt_file.read_text(encoding="utf-8", errors="ignore").strip()
        if len(text) < 500:
            skipped += 1
            continue

        cleaned_text = clean_text(text)
        filename_clean = re.sub(r"\b(20\d{2})(?:[-_]\d{4})?\b", "", normalize(txt_file.stem)).strip()
        match = metadata_df[metadata_df["company_clean"] == filename_clean]

        if not match.empty:
            subsector = match["subsector"].values[0]
            grouped[subsector].append(cleaned_text)
            matched += 1
        else:
            skipped += 1

    print(f"[✓] Matched {matched} files to subsectors | Skipped {skipped} files.")
    return grouped

def extract_topics_tfidf(grouped_texts: dict, top_n: int = 15) -> pd.DataFrame:
    results = []
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)

    for subsector, docs in grouped_texts.items():
        if len(docs) < 2:
            continue
        try:
            tfidf_matrix = vectorizer.fit_transform(docs)
            feature_array = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.mean(axis=0).A1
            top_indices = scores.argsort()[::-1][:top_n]

            for idx in top_indices:
                results.append({
                    "Subsector": subsector,
                    "Topic": feature_array[idx],
                    "Score": scores[idx]
                })

        except Exception as e:
            print(f"[!] Failed for {subsector}: {e}")

    return pd.DataFrame(results)

if __name__ == "__main__":
    metadata = load_benchmark_metadata()
    grouped_texts = load_and_group_by_subsector(TEXT_ROOT, metadata)
    topic_df = extract_topics_tfidf(grouped_texts)
    topic_df.to_csv(OUTPUT_PATH, index=False)
    print(f"[✔] Saved generated topics to {OUTPUT_PATH}")
