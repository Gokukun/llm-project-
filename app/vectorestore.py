import uuid
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, Document, VectorParams, PointStruct
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to Qdrant
qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    api_key=os.getenv("QDRANT_API_KEY"),
    cloud_inference=True,
)

COLLECTION = "intellentx_docs"

def create_collection():
    """
    Create or recreate Qdrant collection
    """
    qdrant.recreate_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        )
    )

def embed_and_store(chunks: list[str]):
    """
    Embed text chunks and store in Qdrant
    """
    if not chunks:
        return

    points = [
        PointStruct(
            id=str(uuid.uuid4()),   # unique ID every time
            vector=Document(
                text=chunk,
                model="sentence-transformers/all-MiniLM-L6-v2",
            ),
            payload={
                "text": chunk
            }
        )
        for chunk in chunks
    ]

    qdrant.upsert(
        collection_name=COLLECTION,
        points=points
    )
