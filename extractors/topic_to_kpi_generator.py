import pandas as pd
from pathlib import Path
from rapidfuzz import fuzz

INPUT_PATH = Path("data/processed/generated_topics_by_subsector.csv")
OUTPUT_PATH = Path("data/processed/method2_kpi.csv")

# Multi-keyword to KPI mapping
KEYWORD_KPI_MAP = {
    ("energy", "electricity", "power"): "Energy Consumption",
    ("emission", "emissions", "co2", "ghg", "carbon"): "GHG Emissions (Total)",
    ("climate",): "Climate risk exposure",
    ("environment", "environmental"): "Environmental impact score",
    ("solar", "renewable"): "Renewable energy capacity (MW)",
    ("water", "wastewater"): "Total water withdrawn (m³)",
    ("waste", "hazardous"): "Total waste generated (tonnes)",
    
    ("employee", "employees", "workforce"): "Number of employees",
    ("injury", "accident"): "Work-related injuries (cases)",
    ("health", "safety"): "Employee health and safety programs",
    ("training", "hours"): "Average training hours per employee",
    ("development", "community", "communities"): "Community development investment (USD)",
    ("diversity", "inclusion"): "Board gender diversity (%)",
    ("people",): "Workforce well-being initiatives",
    ("sustain", "sustainability"): "Sustainability initiatives",
    
    ("governance", "board"): "Independent board members (%)",
    ("report", "reporting"): "Sustainability report published",
    ("risk",): "Enterprise risk exposure score",
    ("management", "strategy"): "Sustainability governance strategy",
    ("gri",): "GRI compliance level",
    ("compensation",): "Executive compensation ratio",
    ("net zero",): "Net zero target date",
    ("responsible", "sourcing"): "Responsible sourcing practices",
    ("privacy", "data"): "Customer data privacy complaints",
    
    ("operations", "operational"): "Operational ESG risk score",
    ("fiscal", "fiscal year", "reporting year"): "Fiscal year ESG disclosures",
    ("business", "model"): "ESG risks in business model",
    
    # New fuzzy-added keywords
    ("plant", "factory", "facilities"): "Number of production facilities",
    ("segment", "segmentation"): "ESG segmentation strategy",
    ("comparison", "benchmark"): "ESG performance benchmark",
    ("aviation", "aircraft", "flight"): "Airline GHG emissions (Scope 1)",
    ("games", "gaming"): "Ethical impact of gaming content",
    ("ceo", "president", "leadership"): "Leadership ESG accountability",
    ("cancer", "health risk"): "Occupational health risk programs",
    ("japan", "taiwan", "russian"): "Country-specific ESG compliance",
    ("colleagues", "staff"): "Employee inclusion and engagement",
    ("entropy", "loss"): "Operational energy loss indicator",
    ("agriculture", "farming"): "GRI compliance level"
}

def match_topic_to_kpi(topic: str) -> str | None:
    topic_clean = topic.lower()
    best_score = 0
    best_kpi = None

    for keywords, kpi in KEYWORD_KPI_MAP.items():
        for keyword in keywords:
            score = fuzz.partial_ratio(keyword, topic_clean)
            if score > 80 and score > best_score:
                best_score = score
                best_kpi = kpi
    return best_kpi

def generate_kpi_hypotheses(input_path: Path) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    results = []

    for _, row in df.iterrows():
        topic = str(row["Topic"])
        kpi = match_topic_to_kpi(topic)
        if kpi:
            results.append({
                "subsector": row["Subsector"],
                "topic": topic,
                "kpi": kpi
            })

    return pd.DataFrame(results)

if __name__ == "__main__":
    df = generate_kpi_hypotheses(INPUT_PATH)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"[✔] Saved Method 2 KPI hypotheses to {OUTPUT_PATH}")
