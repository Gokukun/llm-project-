import gradio as gr
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/ask")

def ask_backend(message, history):
    try:
        response = requests.get(
            BACKEND_URL,
            params = {"q": message},
            timeout = 30
        )

        data = response.json()
        if response.ok:
            answer = data.get("answer", "No response from the chatbot.")
        else:
            answer = data.get("detail", f"Backend request failed ({response.status_code}).")
    except Exception as e:
        answer = f"Error : {str(e)}"

    return answer

with gr.Blocks(title="chatbot") as demo:
    gr.Markdown("#RANA Meet chatbot")
    gr.Markdown("#Ask Anything about rana meet")

    gr.ChatInterface(
        fn=ask_backend
    )

demo.launch(
    server_name="0.0.0.0",
    server_port=int(os.getenv("PORT", "7860")),
    share=False,
)
