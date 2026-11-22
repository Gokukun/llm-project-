import gradio as gr

from app.chat import answer_query
from app.main import app
from ui import build_demo


def ask_direct(message, history):
    """Answer directly from the RAG pipeline (no internal HTTP request)."""
    try:
        return answer_query(message)
    except Exception as exc:
        return f"Error: {exc}"


demo = build_demo(ask_direct)
gr.mount_gradio_app(app, demo, path="/")
