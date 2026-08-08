import streamlit as st
from chatbot import ask_llama

st.set_page_config(
    page_title="Profile Bot",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.main {
    background-color: #0E1117;
    color: white;
}

.title {
    text-align: center;
    font-size: 52px;
    font-weight: 800;
    background: linear-gradient(90deg, #00C6FF, #0072FF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 10px;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    color: #A0A0A0;
    margin-bottom: 30px;
}

.user-msg {
    background-color: #1E293B;
    padding: 15px;
    border-radius: 15px;
    margin-bottom: 10px;
    font-size: 16px;
}

.bot-msg {
    background-color: #111827;
    padding: 15px;
    border-radius: 15px;
    margin-bottom: 20px;
    border-left: 4px solid #3B82F6;
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image(
        "https://cdn-icons-png.flaticon.com/512/4712/4712027.png",
        width=120
    )
    st.title("About")
    st.write("AI-powered portfolio chatbot for Rana Meet")
    
    st.markdown("---")
    st.write("### Skills")
    st.write("""
    - Python  
    - Machine Learning  
    - Deep Learning  
    - NLP  
    - Streamlit  
    - LangChain  
    """)

    st.markdown("---")
    st.write("Built with ❤️ using Llama + RAG")

# Main page
st.markdown('<div class="title">Profile Bot 🤖</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Ask anything about Rana Meet</div>',
    unsafe_allow_html=True
)

question = st.chat_input("Ask a question...")

if "messages" not in st.session_state:
    st.session_state.messages = []

if question:
    st.session_state.messages.append(("user", question))

    answer = ask_llama(question)
    st.session_state.messages.append(("bot", answer))

# Display chat history
for role, message in st.session_state.messages:
    if role == "user":
        st.markdown(
            f'<div class="user-msg">🧑 {message}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="bot-msg">🤖 {message}</div>',
            unsafe_allow_html=True
        )