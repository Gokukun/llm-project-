import os

import gradio as gr
import requests
from requests.exceptions import JSONDecodeError

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/ask")


def ask_backend(message, history):
    try:
        response = requests.get(
            BACKEND_URL,
            params={"q": message},
            timeout=30,
        )

        try:
            data = response.json()
        except JSONDecodeError:
            return (
                f"Backend returned HTTP {response.status_code}, not JSON. "
                "Check the BACKEND_URL environment variable."
            )

        if response.ok:
            answer = data.get("answer", "No response from the chatbot.")
        else:
            answer = data.get("detail", f"Backend request failed ({response.status_code}).")
    except Exception as e:
        answer = f"Error : {str(e)}"

    return answer


def build_demo(ask_fn=None):
    """Create the Gradio UI. Pass a direct ask function for combined deployments."""
    if ask_fn is None:
        ask_fn = ask_backend

    with gr.Blocks(title="Rana Meet AI Assistant") as demo:
        gr.Markdown("# Rana Meet — AI Portfolio Assistant")
        gr.Markdown(
            "Ask anything about Rana Meet's projects, skills, and experience."
        )

        gr.ChatInterface(
            fn=ask_fn,
            examples=[
                "What projects has Rana worked on?",
                "What are Rana's technical skills?",
                "How can I contact Rana?",
            ],
        )

    return demo


if __name__ == "__main__":
    demo = build_demo()
    demo.launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.getenv("PORT", "7860")),
        share=False,
    )
