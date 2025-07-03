import os
import pdfplumber
import json
import re
import contextlib
import io
from scrapers.utils import get_logger
import warnings

warnings.filterwarnings("ignore")
logger = get_logger("kpi_extractor", log_file="logs/kpi_extractor.log")

# ✅ Expanded regex KPI patterns — 20+ ESG metrics
KPI_PATTERNS = {
    "CO2 Emissions (Scope 1)": r"(?:scope ?1(?: emissions)?|direct CO2 emissions).{0,40}?(\d[\d,\.]+\s?(?:tCO2e|tons|t|MT|million|thousand)?)",
    "CO2 Emissions (Scope 2)": r"(?:scope ?2(?: emissions)?|indirect CO2 emissions).{0,40}?(\d[\d,\.]+\s?(?:tCO2e|tons|t|MT|million|thousand)?)",
    "CO2 Emissions (Scope 3)": r"(?:scope ?3(?: emissions)?).{0,40}?(\d[\d,\.]+\s?(?:tCO2e|tons|t|MT|million|thousand)?)",
    "GHG Emissions (Total)": r"(?:total\s)?GHG emissions.{0,40}?(\d[\d,\.]+\s?(?:tCO2e|tons|t|MT|million|thousand)?)",
    "Carbon Intensity": r"(?:carbon intensity).{0,40}?(\d[\d,\.]+\s?(?:tCO2e\/\w+|kg\/unit|tons\/\w+)?)",
    "Water Usage": r"(?:water (?:consumption|usage|withdrawal)).{0,40}?(\d[\d,\.]+\s?(?:m3|liters|gallons|million|thousand)?)",
    "Energy Consumption": r"(?:total )?energy (?:use|consumption).{0,40}?(\d[\d,\.]+\s?(?:kWh|MWh|GWh|TJ|MJ|GJ)?)",
    "Renewable Energy Usage": r"(?:renewable energy (?:use|usage|consumption)).{0,40}?(\d[\d,\.]+\s?(?:kWh|MWh|%|percent)?)",
    "Electricity Consumption": r"(?:electricity (?:consumption|use)).{0,40}?(\d[\d,\.]+\s?(?:kWh|MWh|GWh)?)",
    "Waste Generated": r"(?:waste (?:generated|produced)).{0,40}?(\d[\d,\.]+\s?(?:tons|kg|MT|million|thousand)?)",
    "Hazardous Waste": r"(?:hazardous waste).{0,40}?(\d[\d,\.]+\s?(?:tons|kg|MT)?)",
    "Recycled Waste": r"(?:recycled waste|recycling rate).{0,40}?(\d[\d,\.]+\s?(?:tons|kg|%|percent)?)",
    "Total Employees": r"(?:number of employees|total headcount).{0,40}?(\d[\d,\.]+)",
    "Women in Workforce": r"(?:female employees|women in (?:workforce|management)).{0,40}?(\d[\d,\.]+\s?(?:%|percent)?)",
    "Employee Turnover": r"(?:employee turnover (?:rate)?).{0,40}?(\d[\d,\.]+\s?(?:%|percent)?)",
    "Training Hours": r"(?:training hours per employee).{0,40}?(\d[\d,\.]+\s?(?:hours)?)",
    "Lost Time Injury Rate": r"(?:lost time injury rate|LTIR).{0,40}?(\d[\d,\.]+)",
    "Safety Incidents": r"(?:workplace accidents|recordable incidents).{0,40}?(\d[\d,\.]+)",
    "Revenue": r"(?:total (?:revenue|sales)).{0,40}?(\d[\d,\.]+\s?(?:USD|EUR|million|billion|thousand)?)",
    "Charitable Donations": r"(?:charitable (?:spending|donations)).{0,40}?(\d[\d,\.]+\s?(?:USD|EUR|million|thousand)?)",
    "Fines and Penalties": r"(?:fines|penalties).{0,40}?(\d[\d,\.]+\s?(?:USD|EUR|million|thousand)?)",
    "Supply Chain Audits": r"(?:supplier audits|supply chain audits).{0,40}?(\d[\d,\.]+)",
    "Board Diversity": r"(?:board diversity|women on board).{0,40}?(\d[\d,\.]+\s?(?:%|percent)?)"
}


def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        with contextlib.redirect_stderr(io.StringIO()):  # 👈 suppress PDF engine spam
            with pdfplumber.open(pdf_path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return ""


def extract_kpis(text: str) -> dict:
    kpis = {}
    for key, pattern in KPI_PATTERNS.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            kpis[key] = match.group(1).strip()
    return kpis


def process_all_pdfs(input_dir="data/raw/", output_path="data/processed/kpi_extraction.json"):
    results = []

    for root, _, files in os.walk(input_dir):
        for file in files:
            if not file.endswith(".pdf"):
                continue

            full_path = os.path.join(root, file)
            logger.info(f"🔍 Processing: {file}")
            text = extract_text_from_pdf(full_path)
            if not text:
                continue

            try:
                name_part = file.replace(".pdf", "")
                company, year = name_part.rsplit("__", 1)
            except ValueError:
                company, year = file.replace(".pdf", ""), "Unknown"

            kpi_data = extract_kpis(text)

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

    logger.info(f"[✔] Extraction complete. Saved {len(results)} entries to {output_path}")
    print(f"[✔] KPI extraction complete → {output_path}")


if __name__ == "__main__":
    process_all_pdfs()
