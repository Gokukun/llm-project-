from bs4 import BeautifulSoup
import requests


def fetch_page_text(url: str) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": "RanaMeetChatbot/1.0"},
        timeout=30,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)
