from app.scraping import fetch_page_text
from langchain_text_splitters import RecursiveCharacterTextSplitter

def ingest_pages(urls: list[str]) -> list[str]:
    chunks = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    for url in urls:
        
        text = fetch_page_text(url)
        
       
        text_chunks = splitter.split_text(text)

       
        formatted_chunks = [chunk.strip() for chunk in text_chunks if chunk.strip()]

        
        chunks.extend(formatted_chunks)

    return chunks
