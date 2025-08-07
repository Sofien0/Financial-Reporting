import os
import streamlit as st
from dotenv import load_dotenv

# 🧠 Langchain & Pinecone
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# 🔐 Charger les variables d'environnement
load_dotenv()
openai_api_key = os.environ.get("OPENAI_API_KEY")
pinecone_api_key = os.environ.get("PINECONE_API_KEY")
index_name = os.environ.get("PINECONE_INDEX_NAME")

# 🧠 Initialisation Pinecone
pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index(index_name)

# 🧠 Embeddings et vecteurs
embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=openai_api_key)
vector_store = PineconeVectorStore(index=index, embedding=embeddings)

# 🌐 Interface Streamlit
st.set_page_config(page_title="📚 Chatbot RAG", layout="centered")
st.title("📚 Chatbot Intelligent RAG")

# 💬 Initialisation de l'historique
if "messages" not in st.session_state:
    st.session_state.messages = [
        SystemMessage(content="You are an assistant for question-answering tasks.")
    ]

# 💬 Affichage de l’historique
for msg in st.session_state.messages:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.markdown(msg.content)

# 📥 Boîte d'entrée utilisateur
prompt = st.chat_input("Posez une question sur vos documents...")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append(HumanMessage(content=prompt))

    # ⚙️ Initialiser le modèle GPT
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=openai_api_key)

    # 🔍 Création du retriever
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 3, "score_threshold": 0.5}
    )
    docs = retriever.invoke(prompt)
    docs_text = "\n\n".join([doc.page_content for doc in docs])

    # 🧠 Création du prompt système avec contexte
    system_prompt = f"""
You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.
Use three sentences maximum and keep the answer concise.

Context: {docs_text}
"""
    st.session_state.messages.append(SystemMessage(content=system_prompt))

    # ✨ Appel LLM
    response = llm.invoke(st.session_state.messages).content

    # 💬 Afficher réponse
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append(AIMessage(content=response))
