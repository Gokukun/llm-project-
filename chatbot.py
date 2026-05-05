import streamlit as st
import bs4
from groq import Groq

from langchain_community.document_loaders import (
    WebBaseLoader,
    PyPDFLoader
)

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


# ---------------- VECTOR STORE ---------------- #

@st.cache_resource
def load_vectorstore():
    try:
        all_docs = []

        # 🌐 Load Website
        try:
            loader2 = WebBaseLoader(
                web_path=("https://gokukun.github.io/ranameet.github.io/",),
                bs_kwargs=dict(
                    parse_only=bs4.SoupStrainer(
                        class_=("post-title", "post-content", "post-header")
                    )
                ),
            )
            docs2 = loader2.load()
            all_docs.extend(docs2)
        except Exception as e:
            st.warning(f"Website load failed: {e}")

        # 📄 Load PDF (only if exists)
        try:
            loader3 = PyPDFLoader("data/MEET RANA.pdf")
            docs3 = loader3.load()
            all_docs.extend(docs3)
        except Exception as e:
            st.warning(f"PDF load failed: {e}")

        if not all_docs:
            st.error("No documents loaded!")
            return None

        # ✂️ Split text
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=300
        )
        split_docs = splitter.split_documents(all_docs)

        # 🤖 Embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # 💾 Vector DB
        db = Chroma.from_documents(
            documents=split_docs,
            embedding=embeddings
        )

        return db

    except Exception as e:
        st.error(f"Vectorstore Error: {e}")
        return None


# Lazy load (VERY IMPORTANT)
db = None


def retrieve_context(query):
    global db
    if db is None:
        db = load_vectorstore()

    if db is None:
        return "No data available."

    results = db.similarity_search(query, k=5)
    return "\n\n".join([doc.page_content for doc in results])


# ---------------- GROQ CLIENT ---------------- #

def get_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except Exception:
        st.error("GROQ API key missing. Add it in Streamlit Secrets.")
        return None


# ---------------- MAIN FUNCTION ---------------- #

def ask_llama(question):
    client = get_client()
    if client is None:
        return "API key not configured."

    context = retrieve_context(question)

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": """
You are a portfolio assistant.

Answer only from provided context.

If the user asks about all projects, list EVERY project found in the context.
Do not summarize into one item if multiple projects exist.
"""
                },
                {
                    "role": "user",
                    "content": f"""
Context:
{context}

Question:
{question}
"""
                }
            ],
            max_tokens=250
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error generating response: {e}"
