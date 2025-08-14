import re
import pandas as pd
from pathlib import Path
from collections import defaultdict
from difflib import get_close_matches

TEXT_ROOT = Path("data/processed/parsed_text")
METADATA_PATH = Path("data/processed/benchmark_long_table_cleaned.csv")
OUTPUT_DIR = Path("data/processed/parsed_text_by_subsector")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def normalize(name: str) -> str:
    name = name.lower()
    name = name.replace("_", " ").replace("-", " ")
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\b(the|sa|inc|plc|ltd|co|corp|nv|spa|llc)\b", "", name)
    name = re.sub(r"\b(19|20)\d{2}\b", "", name)  # remove year
    return name.strip()


# Load company-subsector mapping
df = pd.read_csv(METADATA_PATH)
df["company_clean"] = df["company"].apply(normalize)
company_to_subsector = dict(zip(df["company_clean"], df["subsector"]))

# Build subsector → list of texts
grouped = defaultdict(list)

for txt_file in TEXT_ROOT.glob("*.txt"):
    text = txt_file.read_text(encoding="utf-8", errors="ignore").strip()
    if len(text) < 100:
        continue

    filename_clean = normalize(txt_file.stem)
    match = get_close_matches(filename_clean, company_to_subsector.keys(), n=1, cutoff=0.8)
    if match:
        subsector = company_to_subsector[match[0]]
        grouped[subsector].append(text)
    else:
        print(f"[!] Skipped: {txt_file.name} (normalized: {filename_clean})")

# Save grouped texts
for subsector, docs in grouped.items():
    if pd.isna(subsector):
        print(f"[!] Skipping subsector with NaN value")
        continue
    name = subsector.replace("&", "and").replace("/", "-").replace(" ", "_")
    out_path = OUTPUT_DIR / f"{name}.txt"
    out_path.write_text("\n\n".join(docs), encoding="utf-8")

print(f"[✔] Grouped texts saved to {OUTPUT_DIR}")
