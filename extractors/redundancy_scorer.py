import json
import pandas as pd
from collections import defaultdict, Counter
from pathlib import Path

# --- Paths ---
EXTRACTED_KPI_PATH = "data/processed/kpi_extraction.json"
BENCHMARK_PATH = "data/processed/benchmark_long_table_cleaned.csv"
OUTPUT_PATH = "data/processed/redundancy_scores.csv"

# --- Normalize function to match company names ---
def normalize_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")

# --- Load files ---
def load_data():
    with open(EXTRACTED_KPI_PATH, "r", encoding="utf-8") as f:
        kpi_data = json.load(f)

    df_benchmark = pd.read_csv(BENCHMARK_PATH)
    df_benchmark["company_norm"] = df_benchmark["company"].apply(normalize_name)
    return kpi_data, df_benchmark

# --- Compute redundancy scores ---
def compute_scores(kpi_data, df_benchmark):
    # Group entries by subsector
    subsector_kpis = defaultdict(list)
    subsector_topics = defaultdict(list)

    for entry in kpi_data:
        company_norm = normalize_name(entry["Company"])
        match_row = df_benchmark[df_benchmark["company_norm"] == company_norm]

        if match_row.empty:
            continue  # Skip companies not found
        subsector = match_row["subsector"].values[0]

        for kpi, value in entry.items():
            if kpi in ["Company", "Year", "Topics"]:
                continue
            if not value or not isinstance(value, str):
                continue

            subsector_kpis[subsector].append(kpi)

            # Add all topics for this KPI
            topics = entry.get("Topics", {}).get(kpi, [])
            subsector_topics[subsector].extend(topics)

    # --- Prepare output ---
    rows = []
    for subsector in subsector_kpis:
        kpi_counts = Counter(subsector_kpis[subsector])
        topic_counts = Counter(subsector_topics[subsector])

        for kpi, kpi_score in kpi_counts.items():
            topics = entry.get("Topics", {}).get(kpi, [])
            topic_score = sum(topic_counts.get(t, 0) for t in topics)

            rows.append({
                "Subsector": subsector,
                "KPI": kpi,
                "KPI_Score": kpi_score,
                "Topics": "; ".join(topics),
                "Topic_Score": topic_score
            })

    return pd.DataFrame(rows)

# --- Save ---
def save_scores(df: pd.DataFrame):
    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"[✔] Saved redundancy scores to: {OUTPUT_PATH}")

# --- Run ---
def run_redundancy_scoring():
    kpi_data, df_benchmark = load_data()
    scores_df = compute_scores(kpi_data, df_benchmark)
    save_scores(scores_df)

if __name__ == "__main__":
    run_redundancy_scoring()
