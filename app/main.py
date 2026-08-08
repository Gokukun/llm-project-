from fastapi import FastAPI, Header, HTTPException
from typing import List
import os
import secrets
from app.vectorestore  import create_collection, embed_and_store
from app.ingest import ingest_pages
from app.chat import answer_query

app = FastAPI()


@app.get("/")
def root():
    return {"message": "server is running"}

@app.post("/init")
def init_store(urls: List[str], x_ingest_key: str | None = Header(default=None)):
    expected_key = os.getenv("INGEST_API_KEY")
    if expected_key and not secrets.compare_digest(x_ingest_key or "", expected_key):
        raise HTTPException(status_code=401, detail="Invalid ingestion key")

    create_collection()
    chunks = ingest_pages(urls)
    embed_and_store(chunks)
    return {"status": "ok", "ingested": len(chunks)}


@app.get("/ask")
def ask(q: str):
    try:
        answer = answer_query(q)
        return {"query": q, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
