import pandas as pd
import os
import re

RAW_PDF_ROOT = "data/raw/"

def normalize_company_name(name):
    name = str(name).lower().strip()
    name = re.sub(r'[\s_\.-]+', '', name)
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

def clean_unit(unit):
    if pd.isna(unit):
        return None
    unit = str(unit).strip().lower()
    unit = unit.replace(" ", "")
    if unit in ["t", "tons", "tonnes"]:
        return "t"
    elif unit in ["kg", "kgs"]:
        return "kg"
    elif unit in ["m3", "m³", "cubicmeters"]:
        return "m³"
    elif "%" in unit:
        return "%"
    return unit

def extract_year(y):
    if pd.isna(y):
        return None
    y = str(y)
    match = re.search(r"\b(20\d{2})\b", y)
    return int(match.group(1)) if match else None

def resolve_pdf_path(sector, subsector, company):
    if pd.isna(sector) or pd.isna(subsector):
        return None

    # Normalize folder paths
    folder_sector = sector.strip().replace(" ", "_").replace("&", "and")
    folder_subsector = subsector.strip().replace(" ", "_").replace("&", "and").replace("/", "_").replace("–", "-")
    full_folder = os.path.join(RAW_PDF_ROOT, folder_sector, folder_subsector)

    if not os.path.isdir(full_folder):
        return None

    # Normalize company name for matching
    normalized = normalize_company_name(company)

    # Look for any file containing the normalized name
    for file in os.listdir(full_folder):
        file_normalized = normalize_company_name(file)
        if normalized in file_normalized:
            return os.path.join(full_folder, file)

    return None  # No match found


def build_long_format_benchmark_table(
    kpi_path="data/processed/kpi_table.csv",
    metadata_path="data/processed/sasb_reporters.csv",
    output_path="data/benchmark_long_table.csv"
):
    print("📥 Loading KPI table...")
    kpi_df = pd.read_csv(kpi_path)
    kpi_df.columns = [c.strip().lower().replace(" ", "_") for c in kpi_df.columns]

    print("📥 Loading SASB metadata...")
    meta_df = pd.read_csv(metadata_path)
    meta_df.columns = [c.strip().lower().replace(" ", "_") for c in meta_df.columns]

    print("🧹 Cleaning and normalizing columns...")
    kpi_df["company_clean"] = kpi_df["company"].apply(normalize_company_name)
    meta_df["company_clean"] = meta_df["company_name"].apply(normalize_company_name)

    print("🔗 Merging on cleaned company name...")
    merged = pd.merge(
        kpi_df,
        meta_df[["company_clean", "sector", "industry"]],
        on="company_clean",
        how="left"
    )

    # Drop duplicate kpi_name if present
    if "kpi_name" in merged.columns and "matched_kpi" in merged.columns:
        merged.drop(columns=["kpi_name"], inplace=True)

    merged = merged.rename(columns={
        "matched_kpi": "kpi_name",
        "industry": "subsector"
    })

    print("🧽 Cleaning units and years...")
    merged["unit"] = merged["unit"].apply(clean_unit)
    merged["year"] = merged["year"].apply(extract_year)

    print("🧭 Resolving PDF paths...")
    merged["pdf_path"] = merged.apply(lambda row: resolve_pdf_path(row["sector"], row["subsector"], row["company"]), axis=1)

    # Select and order final columns
    final_cols = ["kpi_name", "company", "value", "unit", "year", "sector", "subsector", "pdf_path"]
    final = merged[final_cols]

    # Report and log unmatched
    matched = final["sector"].notna().sum()
    print(f"✅ Matched sector/subsector for {matched}/{len(final)} entries")

    unmatched = final[final["sector"].isna()]
    if not unmatched.empty:
        os.makedirs("logs", exist_ok=True)
        unmatched[["company"]].drop_duplicates().to_csv("logs/unmatched_companies.csv", index=False)
        print(f"⚠️ Logged {len(unmatched)} unmatched entries to logs/unmatched_companies.csv")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final.to_csv(output_path, index=False)
    print(f"✅ Saved to: {output_path}")
    print("🔍 Preview:")
    print(final.head())

if __name__ == "__main__":
    build_long_format_benchmark_table()
