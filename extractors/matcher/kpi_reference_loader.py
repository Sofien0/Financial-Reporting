import pandas as pd
from sentence_transformers import SentenceTransformer

def load_kpi_targets(excel_path: str, lang: str = "en"):
    df = pd.read_excel(excel_path, sheet_name="Sheet1")
    if lang == "en":
        return df["kpi_name"].dropna().tolist()
    elif lang == "fr":
        return df["kpi_name_fr"].dropna().tolist()
    else:
        raise ValueError("Unsupported language")

def encode_kpis(kpi_list, model=None):
    if model is None:
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    embeddings = model.encode(kpi_list, convert_to_tensor=True)
    return embeddings