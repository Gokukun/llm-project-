import os
import re
import uuid

import psycopg
from dotenv import load_dotenv
from pgvector import Vector
from pgvector.psycopg import register_vector
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

TABLE = "intellentx_docs"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
RRF_K = 60

_model = None
_bm25_cache = None

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase text and split it into word tokens for BM25."""
    return _TOKEN_RE.findall(text.lower())


def get_model() -> SentenceTransformer:
    """Load the embedding model once per process."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg.connect(DATABASE_URL)


def _invalidate_bm25_cache():
    """Drop the cached BM25 index after the document table changes."""
    global _bm25_cache
    _bm25_cache = None


def create_collection():
    """
    Recreate the pgvector table and its similarity index.
    """
    _invalidate_bm25_cache()

    with get_connection() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute(f"DROP TABLE IF EXISTS {TABLE}")
        conn.execute(
            f"""
            CREATE TABLE {TABLE} (
                id uuid PRIMARY KEY,
                text text NOT NULL,
                embedding vector({EMBEDDING_DIM}) NOT NULL
            )
            """
        )
        conn.execute(
            f"""
            CREATE INDEX {TABLE}_embedding_idx
            ON {TABLE} USING hnsw (embedding vector_cosine_ops)
            """
        )

    _invalidate_bm25_cache()


def embed_and_store(chunks: list[str]):
    """
    Embed text chunks and store them in PostgreSQL with pgvector.
    """
    if not chunks:
        return

    embeddings = get_model().encode(chunks, normalize_embeddings=True)

    with get_connection() as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.executemany(
                f"INSERT INTO {TABLE} (id, text, embedding) VALUES (%s, %s, %s)",
                [
                    (str(uuid.uuid4()), chunk, Vector(embedding.tolist()))
                    for chunk, embedding in zip(chunks, embeddings)
                ],
            )

    _invalidate_bm25_cache()


def _get_bm25_index() -> tuple[list[str], list[str], BM25Okapi] | None:
    """Build and cache a BM25 index from every stored chunk."""
    global _bm25_cache
    if _bm25_cache is not None:
        return _bm25_cache

    with get_connection() as conn:
        rows = conn.execute(f"SELECT id::text, text FROM {TABLE}").fetchall()

    if not rows:
        return None

    ids = [row[0] for row in rows]
    texts = [row[1] for row in rows]
    _bm25_cache = (ids, texts, BM25Okapi([tokenize(text) for text in texts]))
    return _bm25_cache


def search_vector(query: str, k: int = 5) -> list[tuple[str, str]]:
    """Return (id, text) for the k nearest vectors."""
    embedding = get_model().encode(query, normalize_embeddings=True)

    with get_connection() as conn:
        register_vector(conn)
        rows = conn.execute(
            f"""
            SELECT id::text, text
            FROM {TABLE}
            ORDER BY embedding <=> %s
            LIMIT %s
            """,
            (Vector(embedding.tolist()), k),
        ).fetchall()

    return [(row[0], row[1]) for row in rows]


def search_bm25(query: str, k: int = 5) -> list[tuple[str, str]]:
    """Return (id, text) for the k highest BM25-scoring chunks."""
    index = _get_bm25_index()
    if index is None:
        return []

    ids, texts, bm25 = index
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(
        zip(ids, texts, scores),
        key=lambda item: item[2],
        reverse=True,
    )
    return [(doc_id, text) for doc_id, text, _ in ranked[:k]]


def hybrid_search(query: str, k: int = 5) -> list[str]:
    """
    Combine BM25 and vector results with reciprocal rank fusion (RRF).
    """
    candidate_k = max(k * 4, 20)
    vector_hits = search_vector(query, k=candidate_k)
    bm25_hits = search_bm25(query, k=candidate_k)

    scores: dict[str, float] = {}
    texts: dict[str, str] = {}

    for rank, (doc_id, text) in enumerate(vector_hits, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank)
        texts.setdefault(doc_id, text)

    for rank, (doc_id, text) in enumerate(bm25_hits, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank)
        texts.setdefault(doc_id, text)

    ranked_ids = sorted(scores, key=lambda doc_id: scores[doc_id], reverse=True)
    return [texts[doc_id] for doc_id in ranked_ids[:k]]


def search(query: str, k: int = 5, mode: str = "hybrid") -> list[str]:
    """
    Return the text of the k best chunks.

    mode:
        "hybrid" - BM25 + vector search fused with RRF (default)
        "vector" - semantic vector search only
        "bm25"   - keyword BM25 search only
    """
    if mode == "vector":
        return [text for _, text in search_vector(query, k=k)]
    if mode == "bm25":
        return [text for _, text in search_bm25(query, k=k)]
    if mode == "hybrid":
        return hybrid_search(query, k=k)
    raise ValueError(f"Unknown search mode: {mode}")
