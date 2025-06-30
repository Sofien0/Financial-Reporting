import os
import pdfplumber
import json
import re

from scrapers.utils import get_logger
import warnings
warnings.filterwarnings("ignore")

logger = get_logger("kpi_extractor", log_file="logs/kpi_extractor.log")

# Example regexes (expand later)
KPI_PATTERNS = {
    "CO2 Emissions": r"(?:CO2|carbon dioxide).{0,30}?(\d[\d,\.]+\s?(?:tons|t|MT|million|thousand)?)",
    "Water Usage": r"(?:water (?:consumption|usage)).{0,30}?(\d[\d,\.]+\s?(?:m3|liters|gallons|million|thousand)?)",
    "Energy Consumption": r"(?:energy consumption).{0,30}?(\d[\d,\.]+\s?(?:kWh|MWh|GWh|TJ|MJ)?)",
    "Employees": r"(?:number of employees).{0,30}?(\d[\d,\.]+)",
    "Waste Generated": r"(?:waste (?:generated|produced)).{0,30}?(\d[\d,\.]+\s?(?:tons|kg|MT|million|thousand)?)"
}


def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return ""


def extract_kpis(text: str) -> dict:
    kpis = {}
    for key, pattern in KPI_PATTERNS.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            kpis[key] = match.group(1)
    return kpis


def process_all_pdfs(input_dir: str, output_path: str):
    results = []

    for root, _, files in os.walk(input_dir):
        for file in files:
            if not file.endswith(".pdf"):
                continue

            full_path = os.path.join(root, file)
            logger.info(f"Processing: {file}")
            text = extract_text_from_pdf(full_path)
            kpi_data = extract_kpis(text)

            # Extract company + year from filename convention
            try:
                name_part = file.replace(".pdf", "")
                company, year = name_part.rsplit("__", 1)
            except ValueError:
                company, year = file.replace(".pdf", ""), "Unknown"

            entry = {
                "Company": company,
                "Year": year,
                **kpi_data
            }
            results.append(entry)

    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Extraction complete. Saved {len(results)} entries to {output_path}")
    print(f"[✔] KPI extraction complete → {output_path}")


if __name__ == "__main__":
    process_all_pdfs("data/raw/", "data/processed/kpi_extraction.json")
