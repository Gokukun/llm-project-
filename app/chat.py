from dotenv import load_dotenv
from langchain_groq import ChatGroq
from app.vectorestore import search
import os

load_dotenv()


llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="openai/gpt-oss-120b"
)


def retrieve_context(query: str, k: int = 5) -> str:
    return "\n\n".join(search(query, k=k, mode="hybrid"))


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
