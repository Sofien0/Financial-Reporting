import pandas as pd
from pathlib import Path

def load_benchmark(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def normalize_paths(df: pd.DataFrame) -> pd.DataFrame:
    # Keep Windows-style backslashes for local filesystem
    df['pdf_path'] = df['pdf_path'].apply(
        lambda p: str(Path(str(p))) if pd.notna(p) else p
    )
    return df

def clean_kpi_names(df: pd.DataFrame) -> pd.DataFrame:
    # Drop all Scope 1/2/3 related rows entirely
    drop_scope_mask = df['kpi_name'].str.contains("Scope 1", case=False, na=False) | \
                      df['kpi_name'].str.contains("Scope 2", case=False, na=False) | \
                      df['kpi_name'].str.contains("Scope 3", case=False, na=False)
    df = df[~drop_scope_mask]

    return df


def filter_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.dropna(subset=['value'])

    # Drop rows where unit is empty but value implies %/tCO2 etc
    df = df[~((df['unit'].isna() | (df['unit'] == '')) & df['value'].astype(str).str.contains(r'[%tT]', regex=True))]
    return df

def deduplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    if 'score' in df.columns:
        df = df.sort_values(by='score', ascending=False)
        return df.drop_duplicates(subset=['company', 'kpi_name', 'year'], keep='first')

    # fallback deduplication using median
    def keep_median(group):
        return group.sort_values('value').iloc[len(group) // 2]
    
    return df.groupby(['company', 'kpi_name', 'year'], group_keys=False).apply(keep_median)

def save_cleaned(df: pd.DataFrame, csv_out='data/processed/benchmark_long_table_cleaned.csv'):
    df.to_csv(csv_out, index=False)
    print(f"[✔] Cleaned benchmark saved to: {csv_out}")

def run_postprocessing(csv_in='data/benchmark_long_table.csv'):
    print("🧹 Starting benchmark postprocessing...")

    df = load_benchmark(csv_in)
    df = normalize_paths(df)
    df = clean_kpi_names(df)
    df = filter_invalid_rows(df)
    df = deduplicate_rows(df)

    save_cleaned(df)
if __name__ == "__main__":
    run_postprocessing()
