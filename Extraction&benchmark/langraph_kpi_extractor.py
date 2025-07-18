import os
import pdfplumber
import pandas as pd
import json
from openai import OpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

# 🔐 Charger les variables d'environnement depuis .env
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 📁 Répertoire contenant les PDF et nom du fichier Excel de sortie
PDF_DIR = r"C:\yassmine\reports\Renewable Resources & Alternative Energy\UnknownSubsector"
OUTPUT_XLSX = "benchmark_kpis.xlsx"

# 📥 Extraction du texte des PDF en chunks
def extract_text_from_pdf(pdf_path, max_pages=5):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            chunks = []
            for i in range(0, len(pdf.pages), max_pages):
                chunk_text = "\n".join(
                    [pdf.pages[j].extract_text() or "" for j in range(i, min(i + max_pages, len(pdf.pages)))]
                )
                if chunk_text.strip():
                    chunks.append(chunk_text)
            return chunks
    except Exception as e:
        print(f"❌ Erreur lecture {pdf_path}: {e}")
        return []

# 🧠 Appel GPT pour extraire les KPIs
def extract_kpis_gpt(input):
    content = input["text"]
    file_name = input["file"]
    print(f"\n📥 Traitement de : {file_name}")

    prompt = f"""
You are an ESG analyst. Extract all ESG KPIs from the following report content.

Return a JSON array where each item includes:
- metric_name
- value
- unit
- year
- company
- page

TEXT:
\"\"\"{content[:12000]}\"\"\"

If no KPI is found, return an empty array: []
Only return a valid JSON array and nothing else.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        output = response.choices[0].message.content.strip()

        if output.startswith("```json"):
            output = output[7:]
        if output.endswith("```"):
            output = output[:-3]
        output = output.strip()

        result = json.loads(output)
        return {"kpis": result, "file": file_name}
    except Exception as e:
        print(f"⚠️ Erreur GPT ou JSON parsing pour {file_name} : {e}")
        return {"kpis": [], "file": file_name}

# 💾 Stockage dans Excel
if not os.path.exists(OUTPUT_XLSX):
    global_kpi_df = pd.DataFrame()
else:
    global_kpi_df = pd.read_excel(OUTPUT_XLSX)

def store_kpis(state):
    global global_kpi_df

    kpis = state.get("kpis", [])
    file = state.get("file", "unknown.pdf")
    all_rows = []

    for kpi in kpis:
        kpi["source_file"] = file
        all_rows.append(kpi)

    df = pd.DataFrame(all_rows)
    global_kpi_df = pd.concat([global_kpi_df, df], ignore_index=True)
    global_kpi_df.to_excel(OUTPUT_XLSX, index=False)

    print(f"✅ KPIs sauvegardés pour : {file}")
    if kpis:
        print(f"\n📊 Résultat extrait :")
        for k in kpis:
            print(f"— {k.get('metric_name')} = {k.get('value')} {k.get('unit')} ({k.get('year')})")
    else:
        print(f"⚠️ Aucun KPI extrait pour : {file}")
    return {}

# 🔁 Graphe LangGraph
graph = StateGraph(dict)
graph.add_node("GPT_KPI_Extractor", extract_kpis_gpt)
graph.add_node("Save_To_XLSX", store_kpis)
graph.set_entry_point("GPT_KPI_Extractor")
graph.add_edge("GPT_KPI_Extractor", "Save_To_XLSX")
graph.add_edge("Save_To_XLSX", END)
app = graph.compile()

# ▶️ Lancer le traitement
for pdf_file in os.listdir(PDF_DIR):
    if pdf_file.endswith(".pdf"):
        full_path = os.path.join(PDF_DIR, pdf_file)
        chunks = extract_text_from_pdf(full_path)
        for i, chunk in enumerate(chunks):
            app.invoke({"text": chunk, "file": f"{pdf_file} - chunk {i+1}"})
