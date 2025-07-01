import json
import re
import os
import csv

from extractors.matcher.sentence_matcher import match_candidate_sentences
from extractors.filters import clean_sentence

def parse_value_and_unit(text):
    match = re.search(r"([\d,\.]+)\s*([a-zA-Z%μ³]+)?", text)
    if not match:
        return "", ""
    raw_value, unit = match.groups()
    value = raw_value.replace(",", "")
    return value, unit or ""

def extract_structured_kpis(
    extraction_path="data/processed/kpi_extraction.json",
    kpi_reference_path="data/esg kpis A+ critical.xlsx",
    threshold=0.6,
    output_csv="data/processed/kpi_table.csv",
    output_json="data/processed/kpi_table.json"
):
    with open(extraction_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    candidates = []
    candidate_metadata = []
    total = 0
    kept = 0

    for entry in data:
        company = entry.get("Company", "Unknown")
        year = entry.get("Year", "Unknown")
        page = entry.get("Page", "N/A")

        for key, value in entry.items():
            if key in {"Company", "Year", "Page"} or not value:
                continue

            total += 1
            sentence = f"{key}: {value}"
            sentence = clean_sentence(sentence)

            if not sentence:
                continue

            kept += 1
            candidates.append(sentence)
            candidate_metadata.append({
                "Company": company,
                "Year": year,
                "Page": page,
                "OriginalKey": key,
                "RawValue": value,
                "Candidate": sentence
            })

    print(f"🔍 Loaded {kept}/{total} cleaned candidates for structuring.")

    if not candidates:
        print("⚠️ No valid candidates to process. Check input or sentence cleaning.")
        return

    matches = match_candidate_sentences(
        candidates=candidates,
        excel_path=kpi_reference_path,
        lang="en",
        threshold=threshold
    )

    if not matches:
        print("⚠️ No matches above threshold. Try lowering threshold or improving candidates.")
        return

    print(f"✅ Matched {len(matches)} candidates → Saving benchmark table...")

    rows = []
    json_rows = []

    for match in matches:
        matched_sentence = match["candidate"]
        score = match["score"]
        matched_kpi = match["matched_kpi"]

        metadata = next((m for m in candidate_metadata if m["Candidate"] == matched_sentence), None)
        if not metadata:
            continue

        value, unit = parse_value_and_unit(metadata["RawValue"])

        row = {
            "Company": metadata["Company"],
            "KPI name": metadata["OriginalKey"],
            "Value": value,
            "Unit": unit,
            "Year": metadata["Year"],
            "Page": metadata["Page"],
            "Matched KPI": matched_kpi,
            "Score": score
        }
        rows.append(row)
        json_rows.append(row)

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    with open(output_json, "w", encoding="utf-8") as jf:
        json.dump(json_rows, jf, indent=2, ensure_ascii=False)

    print(f"[✔] CSV written → {output_csv} ({len(rows)} rows)")
    print(f"[✔] JSON written → {output_json} ({len(json_rows)} entries)")


if __name__ == "__main__":
    extract_structured_kpis()
