import os
import json
import pandas as pd
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment (.env file may still be used for paths/configs)
load_dotenv()

# Paths
MERGED_KPI_PATH = Path("data/processed/merged_kpi_scores.csv")
PARSED_TEXT_DIR = Path("data/processed/parsed_text_by_subsector")
CACHE_PATH = Path("data/processed/questions_cache.json")
OUTPUT_PATH = Path("data/processed/generated_questions.csv")

# Load cache if it exists
if CACHE_PATH.exists():
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        question_cache = json.load(f)
else:
    question_cache = {}

# Few-shot examples embedded in prompt
FEW_SHOT_PROMPT = """
You are an ESG analyst assistant.

Below are a few examples of questions an analyst might ask based on ESG KPIs and topics:

Example 1:  
Subsector: Electric Utilities  
KPI: CO2 Emissions (Scope 1)  
Topics: Greenhouse Gas Emissions  
→ Question: How have Scope 1 CO2 emissions evolved over the past three years for this utility company?

Example 2:  
Subsector: Apparel  
KPI: Water Usage  
Topics: Water Management  
→ Question: What initiatives has the company taken to reduce water usage in its supply chain?

Example 3:  
Subsector: Software & IT Services  
KPI: Total Employees  
Topics: Diversity & Inclusion, Employee Engagement  
→ Question: How does the company track and report on diversity metrics across its employee base?
"""

def load_parsed_text_for_subsector(subsector: str) -> str:
    if not isinstance(subsector, str) or pd.isna(subsector):
        return ""
    filename = f"{subsector.replace('/', '-').replace('&', 'and').replace(' ', '_')}.txt"
    file_path = PARSED_TEXT_DIR / filename
    if file_path.exists():
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        return text[:1000]  # Reduced to avoid timeout with local model
    return ""

def build_prompt(subsector: str, kpi: str, topics: list[str], context: str) -> list[dict]:
    prompt = FEW_SHOT_PROMPT.strip()
    user_message = f"""
Now generate a question for this KPI:
Subsector: {subsector}
KPI: {kpi}
Topics: {', '.join(topics)}
"""
    if context:
        user_message += f"(You can use the following context from company reports if helpful: {context})"

    return [
        {"role": "system", "content": "You are an expert ESG analyst assistant. Generate clear questions based on KPI, topic, and context."},
        {"role": "user", "content": prompt + "\n\n---\n" + user_message.strip()}
    ]

def generate_question(messages: list[dict]) -> str:
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "mistral",
            "messages": messages,
            "stream": False
        },
        timeout=60
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()

def main():
    df = pd.read_csv(MERGED_KPI_PATH)
    results = []

    for _, row in df.iterrows():
        subsector = row["Subsector"]
        kpi = row["KPI"]
        topics = eval(row["Topics"]) if isinstance(row["Topics"], str) else row["Topics"]

        cache_key = f"{subsector}::{kpi}"
        if cache_key in question_cache:
            question = question_cache[cache_key]
        else:
            print(f"⏳ Generating: {cache_key}")
            context = load_parsed_text_for_subsector(subsector)
            messages = build_prompt(subsector, kpi, topics, context)
            try:
                question = generate_question(messages)
            except Exception as e:
                print(f"[!] Error for {cache_key}: {e}")
                continue
            question_cache[cache_key] = question

        results.append({
            "Subsector": subsector,
            "KPI": kpi,
            "Topics": topics,
            "Question": question,
            "KPI_Score": row.get("KPI_Score", ""),
            "Topic_Score": row.get("Topic_Score", "")
        })

    # Save output
    pd.DataFrame(results).to_csv(OUTPUT_PATH, index=False)
    print(f"[✔] Saved generated questions to {OUTPUT_PATH}")

    # Save cache
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(question_cache, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
