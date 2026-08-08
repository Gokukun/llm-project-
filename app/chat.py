from qdrant_client import QdrantClient
from qdrant_client.models import Document
from dotenv import load_dotenv
from langchain_groq import ChatGroq  
import os

load_dotenv()


llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile"
)


qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    api_key=os.getenv("QDRANT_API_KEY"),
    cloud_inference=True,
)

COLLECTION = "intellentx_docs"


def retrieve_context(query: str, k: int = 5) -> str:
    hits = qdrant.query_points(
        collection_name=COLLECTION,
        query=Document(
            text=query,
            model="sentence-transformers/all-MiniLM-L6-v2",
        ),
        limit=k,
        with_payload=True,
    )

    return "\n\n".join(
        point.payload["text"] for point in hits.points
    )


def answer_query(query: str) -> str:
    context = retrieve_context(query)

    prompt = f"""
You are the official AI assistant of Rana Meet.

Only answer using the provided context.
If the answer is not found, say:
"I'm not sure based on the available information."

CONTEXT:
{context}

QUESTION:
{query}
"""

    response = llm.invoke(prompt)

    return response.content


if __name__ == "__main__":
    query = input("Ask Question: ")
    answer = answer_query(query)
    print("\nAnswer:\n")
    print(answer)
