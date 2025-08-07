import os
import re
import pandas as pd
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# 📥 Charger le fichier CSV contenant les liens
csv_path = "sasb_reports_completed.csv"
df = pd.read_csv(csv_path)

# 📂 Nouveau dossier d'organisation
base_dir = "reports"

# 🧽 Nettoyer les noms
def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", str(name))

# 📥 Fonction de téléchargement
def download_report(row):
    company = clean_filename(row["Company Name"])
    year = row["Report Year"]
    url = row["Report Link"]

    if not url or pd.isna(url):
        return "🔸 Aucune URL"

    sector = clean_filename(str(row.get("Sector", "UnknownSector")))
    subsector = clean_filename(str(row.get("Subsector", "UnknownSubsector")))
    folder = os.path.join(base_dir, sector, subsector)
    os.makedirs(folder, exist_ok=True)

    filename = f"{company}_{year}_Report.pdf"
    dest_path = os.path.join(folder, filename)

    if os.path.exists(dest_path):
        return "🟡 Déjà téléchargé"

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, stream=True, headers=headers, timeout=15)
        if response.status_code == 200:
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return "✅ Téléchargé"
        else:
            return f"❌ {response.status_code}"
    except Exception as e:
        return f"⚠️ {str(e)}"

# 🧵 Téléchargement parallèle (max 10 threads)
results = [None] * len(df)

print(f"📊 Début du téléchargement parallèle ({len(df)} rapports)...")
with ThreadPoolExecutor(max_workers=10) as executor:
    future_to_index = {executor.submit(download_report, row): i for i, row in df.iterrows()}
    for future in tqdm(as_completed(future_to_index), total=len(future_to_index), desc="📥 Téléchargement"):
        i = future_to_index[future]
        try:
            result = future.result()
        except Exception as e:
            result = f"⚠️ Exception: {str(e)}"
        results[i] = result

# ➕ Ajouter la colonne "Download Result"
df["Download Result"] = results

# 💾 Sauvegarde CSV
df.to_csv("sasb_reports_results.csv", index=False, encoding="utf-8-sig")
print("\n✅ Fichier 'sasb_reports_results.csv' mis à jour avec les résultats.")

# 📊 Affichage
import ace_tools as tools
tools.display_dataframe_to_user(name="Résultats Téléchargement ESG", dataframe=df)
