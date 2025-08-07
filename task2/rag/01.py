# 📦 Importations de base
import os
import time
import pandas as pd
from dotenv import load_dotenv

# 🧠 Pinecone + LangChain
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

# 🔁 Chargement des variables d'environnement
load_dotenv()

# 🔑 Initialisation de Pinecone
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index_name = os.environ.get("PINECONE_INDEX_NAME")

# 📦 Créer l'index s'il n'existe pas
existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=3072,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
    while not pc.describe_index(index_name).status["ready"]:
        time.sleep(1)

# 🎯 Connexion à l'index
index = pc.Index(index_name)

# 🤖 Modèle d'embedding
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    api_key=os.environ.get("OPENAI_API_KEY")
)

# 📚 Chargement du fichier Excel
file_path = "documents/questions_par_kpi.xlsx"
if not os.path.exists(file_path):
    raise FileNotFoundError(f"❌ Fichier '{file_path}' introuvable.")

df = pd.read_excel(file_path)

if "Question" not in df.columns:
    raise ValueError("❌ La colonne 'Question' est requise dans le fichier Excel.")

# 📄 Conversion des lignes en documents
documents = [
    Document(page_content=str(row["Question"]), metadata=row.to_dict())
    for _, row in df.iterrows()
]

# 🔢 Génération des UUIDs
uuids = [f"id{i+1}" for i in range(len(documents))]

# 🧠 Vectorisation
vector_store = PineconeVectorStore(index=index, embedding=embeddings)
vector_store.add_documents(documents=documents, ids=uuids)

print(f"✅ {len(documents)} questions vectorisées avec succès dans Pinecone !")
