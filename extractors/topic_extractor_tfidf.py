import re
import pandas as pd
from pathlib import Path
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from difflib import get_close_matches

TEXT_ROOT = Path("data/processed/parsed_text")
BENCHMARK_PATH = Path("data/processed/benchmark_long_table_cleaned.csv")
OUTPUT_PATH = Path("data/processed/generated_topics_by_subsector.csv")

def clean_text(text: str) -> str:
    lines = text.splitlines()
    lines = [line.strip() for line in lines if len(line.strip()) > 5]
    lines = [line for line in lines if not re.search(r"page \d+|esg|contents|©", line, re.IGNORECASE)]
    return " ".join(lines)

def normalize(name: str) -> str:
    name = name.replace("_", " ").replace("-", " ")
    name = re.sub(r"[^\w\s]", "", name)  # Remove punctuation
    name = name.lower().strip()
    name = re.sub(r"\bthe$", "", name).strip()  # Remove trailing 'the'
    return name
def load_benchmark_metadata() -> pd.DataFrame:
    df = pd.read_csv(BENCHMARK_PATH)
    df["company_clean"] = df["company"].apply(normalize)
    return df[["company_clean", "sector", "subsector"]].drop_duplicates()

def load_and_group_by_subsector(text_root: Path, metadata_df: pd.DataFrame) -> dict:
    grouped = defaultdict(list)
    matched, skipped = 0, 0

    for txt_file in text_root.glob("*.txt"):
        text = txt_file.read_text(encoding="utf-8", errors="ignore").strip()
        if len(text) < 100:
            skipped += 1
            continue

        cleaned_text = clean_text(text)
        filename_clean = re.sub(r"\b(20\d{2})(?:[-_]\d{4})?\b", "", normalize(txt_file.stem)).strip()
        possible_matches = get_close_matches(filename_clean, metadata_df["company_clean"], n=1, cutoff=0.7)

        if possible_matches:
            match = metadata_df[metadata_df["company_clean"] == possible_matches[0]]
        else:
            match = metadata_df[metadata_df["company_clean"] == filename_clean]

        if not match.empty:
            subsector = match["subsector"].values[0]
            grouped[subsector].append(cleaned_text)
            matched += 1
        else:
            print(f"[!] Skipped: {txt_file.stem} (normalized: '{filename_clean}')")
            skipped += 1

    print(f"[✓] Matched {matched} files to subsectors | Skipped {skipped} files.")
    return grouped

def auto_stopwords(metadata_df, grouped_texts):
    # Company names from metadata
    company_names = set(metadata_df['company_clean'].unique())
    # Years from all texts
    years = set()
    for docs in grouped_texts.values():
        for text in docs:
            years.update(re.findall(r"\b(20\d{2})\b", text))
    # Very common words across all docs (appearing in >80% of subsectors)
    word_doc_freq = defaultdict(int)
    total_subsectors = len(grouped_texts)
    for docs in grouped_texts.values():
        words = set()
        for text in docs:
            words.update(re.findall(r"\b\w+\b", text.lower()))
        for word in words:
            word_doc_freq[word] += 1
    common_words = {w for w, freq in word_doc_freq.items() if freq / total_subsectors > 0.8}
    # Combine with sklearn's stopwords
    return ENGLISH_STOP_WORDS.union(company_names, years, common_words)

def is_valid_topic(topic, stopwords):
    if topic in stopwords:
        return False
    if topic.isdigit() or len(topic) < 3:
        return False
    if re.fullmatch(r"\d{4}", topic):  # single years like '2023'
        return False
    if re.fullmatch(r"[a-z]{2,4}", topic):  # likely acronyms like 'aaon', 'aar'
        return False
    if re.search(r"\b(form|report|appendix|contents|overview|page|table|cover|gri|10k|fy|202\d)\b", topic):
        return False
    return True


def extract_topics_tfidf(grouped_texts: dict, metadata_df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    results = []
    stopwords = auto_stopwords(metadata_df, grouped_texts)
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=5000)

    for subsector, docs in grouped_texts.items():
        if len(docs) < 2:
            continue
        try:
            tfidf_matrix = vectorizer.fit_transform(docs)
            feature_array = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.mean(axis=0).A1
            top_indices = scores.argsort()[::-1][:top_n*2]  # get more, filter later

            count = 0
            for idx in top_indices:
                topic = feature_array[idx]
                if not is_valid_topic(topic, stopwords):
                    continue
                results.append({
                    "Subsector": subsector,
                    "Topic": topic,
                    "Score": scores[idx]
                })
                count += 1
                if count >= top_n:
                    break

        except Exception as e:
            print(f"[!] Failed for {subsector}: {e}")

    return pd.DataFrame(results)

if __name__ == "__main__":
    metadata = load_benchmark_metadata()
    grouped_texts = load_and_group_by_subsector(TEXT_ROOT, metadata)
    topic_df = extract_topics_tfidf(grouped_texts, metadata)
    topic_df.to_csv(OUTPUT_PATH, index=False)
    print(f"[✔] Saved generated topics to {OUTPUT_PATH}")