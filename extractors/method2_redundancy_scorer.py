import pandas as pd
from pathlib import Path

INPUT_PATH = Path("data/processed/method2_kpi.csv")
OUTPUT_PATH = Path("data/processed/redundancy_score_method2.csv")

def score_kpis(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["subsector", "kpi"])
        .agg({
            "topic": lambda x: list(set(x)),
        })
        .reset_index()
    )
    grouped["Topic_Score"] = grouped["topic"].apply(len)
    grouped["KPI_Score"] = grouped["Topic_Score"]  # can later be weighted differently
    grouped = grouped.rename(columns={
        "subsector": "Subsector",
        "kpi": "KPI",
        "topic": "Topics"
    })
    return grouped[["Subsector", "KPI", "KPI_Score", "Topics", "Topic_Score"]]

if __name__ == "__main__":
    df = pd.read_csv(INPUT_PATH)
    result = score_kpis(df)
    result.to_csv(OUTPUT_PATH, index=False)
    print(f"[✔] Saved Method 2 redundancy scores to {OUTPUT_PATH}")
