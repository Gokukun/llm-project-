import streamlit as st
import bs4
from groq import Groq

from huggingface_hub import InferenceClient

from langchain_community.document_loaders import (
    TextLoader,
    WebBaseLoader,
    PyPDFLoader
)

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


@st.cache_resource
def load_vectorstore():
    # Load text file
    

    # Load website
    loader2 = WebBaseLoader(
        web_path=("https://gokukun.github.io/ranameet.github.io/",),
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer(
                class_=("post-title", "post-content", "post-header")
            )
        ),
    )
    docs2 = loader2.load()

    # Load PDF
    loader3 = PyPDFLoader("MEET RANA.pdf")
    docs3 = loader3.load()

    # Combine documents
    all_docs =  docs2 + docs3

    # Split text
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=300
    )

    split_docs = splitter.split_documents(all_docs)

    # Embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Vector DB
    db = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings
    )

    return db


db = load_vectorstore()

# Hugging Face client
client = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
)

def retrieve_context(query):
    results = db.similarity_search(query, k=10)
    context = "\n\n".join([doc.page_content for doc in results])
    return context

def ask_llama(question):
    context = retrieve_context(question)

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages = [
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
