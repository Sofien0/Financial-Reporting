import os
import pandas as pd
from langchain.agents import initialize_agent, AgentType
from langchain_community.chat_models import ChatOpenAI
from langchain.tools import Tool
from langchain_community.utilities.serpapi import SerpAPIWrapper
from dotenv import load_dotenv

# ✅ Charger les variables d’environnement
load_dotenv()

# 🧠 Initialiser SerpAPI
print("🧠 Initialisation de SerpAPIWrapper...")
search = SerpAPIWrapper()

# 🔧 Définir les outils pour l’agent LangChain
tools = [
    Tool(
        name="Recherche ESG",
        func=search.run,
        description="Recherche Google intelligente pour trouver des rapports ESG PDF"
    )
]

# 🤖 Initialisation de l'agent GPT avec outils
print("🤖 Initialisation de l'agent LangChain avec GPT...")
agent = initialize_agent(
    tools=tools,
    llm=ChatOpenAI(temperature=0),
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# 📥 Charger les données depuis le CSV
csv_path = "C:/yassmine/sasb_reports_selenium.csv"
print(f"📂 Chargement du fichier CSV : {csv_path}")
df = pd.read_csv(csv_path)

print(f"📊 Nombre total d'entreprises : {len(df)}")
missing_links = df[df["Report Link"] == ""]
print(f"🔎 Lignes sans lien : {len(missing_links)}")

# 🔁 Boucle de recherche automatique
for idx, row in missing_links.iterrows():
    company = row["Company Name"]
    year = row["Report Year"]
    domain = company.lower().replace(" ", "")
    query = f"{year} sustainability report site:{domain}.com filetype:pdf"

    print(f"\n🚀 Recherche #{idx + 1} — {company} ({year})")
    print(f"🔎 Requête : {query}")

    try:
        result = agent.run(query)
        df.at[idx, "Report Link"] = result
        df.at[idx, "Source"] = "LangChain-Google"
        print(f"✅ Résultat : {result}")
    except Exception as e:
        df.at[idx, "Source"] = "Not Found"
        print(f"❌ Erreur : {e}")

# 💾 Enregistrement des résultats dans un nouveau CSV
output_path = "C:/yassmine/sasb_reports_completed.csv"
df.to_csv(output_path, index=False, encoding="utf-8-sig")
print(f"\n✅ Fichier exporté : {output_path}")
