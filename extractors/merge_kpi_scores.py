import pandas as pd
from pathlib import Path

METHOD1_PATH = Path("data/processed/redundancy_scores.csv")
METHOD2_PATH = Path("data/processed/redundancy_score_method2.csv")
OUTPUT_PATH = Path("data/processed/merged_kpi_scores.csv")

def load_and_prepare(path, is_method2=False):
    df = pd.read_csv(path)
    df["KPI_Score"] = df["KPI_Score"].fillna(0).astype(int)
    df["Topic_Score"] = df["Topic_Score"].fillna(0).astype(int)
    if not is_method2:
        # Split comma-separated topics into lists, handle empty strings
        df["Topics"] = df["Topics"].fillna("").apply(lambda x: [t.strip() for t in x.split(",") if t.strip()] if x else [])
    return df

def merge_scores(df1, df2):
    # Merge on Subsector + KPI
    merged = pd.merge(df1, df2, on=["Subsector", "KPI"], how="outer", suffixes=("_m1", "_m2"))

    # Combine scores
    merged["KPI_Score"] = merged[["KPI_Score_m1", "KPI_Score_m2"]].fillna(0).astype(int).sum(axis=1)
    merged["Topic_Score"] = merged[["Topic_Score_m1", "Topic_Score_m2"]].fillna(0).astype(int).sum(axis=1)

    # Combine topics (union)
    def merge_topics(row):
        t1 = row["Topics_m1"] if isinstance(row["Topics_m1"], list) else []
        t2 = row["Topics_m2"] if isinstance(row["Topics_m2"], list) else []
        return list(set(t1) | set(t2))

    merged["Topics"] = merged.apply(merge_topics, axis=1)

    # Final score
    merged["Total_Score"] = merged["KPI_Score"] + merged["Topic_Score"]

    # Select final columns
    return merged[["Subsector", "KPI", "KPI_Score", "Topics", "Topic_Score", "Total_Score"]].sort_values(by="Total_Score", ascending=False)

if __name__ == "__main__":
    df1 = load_and_prepare(METHOD1_PATH, is_method2=False)
    df2 = load_and_prepare(METHOD2_PATH, is_method2=True)

    merged = merge_scores(df1, df2)
    merged.to_csv(OUTPUT_PATH, index=False)
    print(f"[✔] Saved merged KPI scores to {OUTPUT_PATH}")
