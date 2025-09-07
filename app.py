import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Load API key from .env
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"
llm_model = "llama-3.3-70b-versatile"

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# RAG setup
if "embedding_model" not in st.session_state:
    st.session_state.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    documents = [
        "The capital of France is Paris.",
        "Python is a popular programming language.",
        "Machine learning is a subset of artificial intelligence.",
        "The Eiffel Tower is in Paris.",
        "Groq provides fast AI inference."
    ]
    embeddings = st.session_state.embedding_model.encode(documents)
    embeddings = np.array(embeddings).astype('float32')
    st.session_state.index = faiss.IndexFlatL2(embeddings.shape[1])
    st.session_state.index.add(embeddings)
    st.session_state.documents = documents

# Dropdown to select chatbot
chatbot_type = st.selectbox(
    "Choose your chatbot:",
    ["Simple Chatbot", "Conversation-History Chatbot", "RAG Chatbot"]
)

st.title(f"{chatbot_type}")

# User input
user_input = st.text_input("Type your message:", value=st.session_state.user_input, key="input_box")
submit = st.button("Send")

# Function to call Groq API
def get_groq_response(messages):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": llm_model,
        "messages": messages
    }
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            return f"Error: {response.status_code} - {response.text}"
    except requests.RequestException as e:
        return f"API Error: {str(e)}"

# Function to retrieve documents for RAG
def retrieve_documents(query, top_k=3):
    query_emb = st.session_state.embedding_model.encode([query])
    query_emb = np.array(query_emb).astype('float32')
    distances, indices = st.session_state.index.search(query_emb, top_k)
    return [st.session_state.documents[i] for i in indices[0]]

# Handle submission
if submit and user_input:
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.history.append({"role": "user", "content": user_input, "time": timestamp})

    # Generate response based on chatbot type
    if chatbot_type == "Simple Chatbot":
        response = f"Echo: {user_input}"
    elif chatbot_type == "Conversation-History Chatbot":
        # Prepare full conversation messages for Groq API
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        for msg in st.session_state.history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        response = get_groq_response(messages)
    elif chatbot_type == "RAG Chatbot":
        retrieved_docs = retrieve_documents(user_input)
        context = "\n".join([f"- {doc}" for doc in retrieved_docs])
        prompt = f"""
You are a concise assistant. Use the context to answer the query. If no info is relevant, say: "Can't provide a valid answer."

Context:
{context}

Query: {user_input}

Answer:
"""
        messages = [{"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}]
        response = get_groq_response(messages)
    else:
        response = "I don't know how to respond."

    st.session_state.history.append({"role": "assistant", "content": response, "time": timestamp})
    st.session_state.user_input = ""

    # Rerun script to refresh UI
    from streamlit.runtime.scriptrunner import RerunException, rerun
    raise RerunException(rerun)

# Display conversation
st.subheader("Conversation")
for msg in st.session_state.history:
    if msg["role"] == "user":
        st.markdown(f"**🧑 You [{msg['time']}]**: {msg['content']}")
    else:
        st.markdown(f"**🤖 Bot [{msg['time']}]**: {msg['content']}")
