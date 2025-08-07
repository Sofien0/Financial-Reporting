# import basics
import os
from dotenv import load_dotenv

# import pinecone
from pinecone import Pinecone

# import langchain
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

# 🧬 Charger les variables d'environnement
load_dotenv()

# 🔑 Initialiser Pinecone
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))

# 📦 Connexion à l'index
index_name = os.environ.get("PINECONE_INDEX_NAME")
index = pc.Index(index_name)

# 🧠 Embeddings + Vector Store
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    api_key=os.environ.get("OPENAI_API_KEY")
)
vector_store = PineconeVectorStore(index=index, embedding=embeddings)

# 🔍 Création du Retriever
retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 5, "score_threshold": 0.6},
)

# 🧪 Requête
query = "c'était quoi la conclusion ?"
results = retriever.invoke(query)

# 📤 Affichage des résultats
print("🔎 Résultats pour la question :", query)
print("────────────────────────────────────────")

if not results:
    print("❌ Aucun résultat trouvé.")
else:
    for i, res in enumerate(results, 1):
        source = res.metadata.get("source", "PDF")
        print(f"[{i}] Source: {source}")
        print(f"→ {res.page_content.strip()}")
        print(f"🧾 Métadonnées : {res.metadata}")
        print("────────────────────────────────────────")
