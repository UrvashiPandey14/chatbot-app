import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

st.set_page_config(page_title="Multi-Chatbot App", layout="wide")

# Theme selection
theme = st.sidebar.radio("Select Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown(
        """
        <style>
        .stApp {background-color: #222; color: #fff;}
        .message {padding:8px; border-radius:8px; margin:5px 0; display:flex; align-items:flex-start;}
        .user {background-color:#0084ff; color:#fff; justify-content:flex-end;}
        .bot {background-color:#00c853; color:#fff; justify-content:flex-start;}
        .avatar {margin-right:8px; font-size:1.2em;}
        .context {background-color:#f1f1f1; color:#000; padding:5px; border-radius:5px; margin:2px 0;}
        </style>
        """, unsafe_allow_html=True
    )

# Dropdown to select chatbot
chatbot_type = st.sidebar.selectbox(
    "Select Chatbot",
    ["General Chatbot", "System Prompt Chatbot", "RAG Chatbot"]
)

# Initialize conversation history for each bot
if "conversations" not in st.session_state:
    st.session_state.conversations = {
        "General Chatbot": [],
        "System Prompt Chatbot": [],
        "RAG Chatbot": []
    }

if "retrieved_context" not in st.session_state:
    st.session_state.retrieved_context = []

# Input box
user_input = st.text_area("Type your message", height=60, key="user_input")
send_button = st.button("Send")

# Assign avatars
bot_avatars = {
    "General Chatbot": "🤖",
    "System Prompt Chatbot": "💡",
    "RAG Chatbot": "📚"
}
user_avatar = "🙂"

# Function to get response from Groq API
def get_groq_response(messages, model="llama-3.3-70b-versatile", temperature=0.4):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

# Display conversation
st.subheader(f"{chatbot_type} Conversation")
conversation = st.session_state.conversations[chatbot_type]

if send_button and user_input.strip() != "":
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conversation.append({"role": "user", "content": user_input.strip(), "timestamp": timestamp})
    
    with st.spinner("Bot is typing..."):
        # Prepare messages
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in conversation]
        
        # Add context for RAG
        if chatbot_type == "RAG Chatbot":
            context_text = "\n".join([f"- {doc}" for doc in st.session_state.retrieved_context])
            if context_text:
                messages.append({"role": "system", "content": f"Retrieved context:\n{context_text}"})
        
        bot_response = get_groq_response(messages)
    
    timestamp_bot = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conversation.append({"role": "bot", "content": bot_response, "timestamp": timestamp_bot})
    
    # Clear input box
    st.session_state.user_input = ""

# Render conversation with avatars
for msg in conversation:
    role_class = "user" if msg["role"] == "user" else "bot"
    avatar = user_avatar if msg["role"] == "user" else bot_avatars.get(chatbot_type, "🤖")
    st.markdown(
        f"<div class='message {role_class}'><span class='avatar'>{avatar}</span><b>{msg['role'].capitalize()}</b> [{msg['timestamp']}]: {msg['content']}</div>",
        unsafe_allow_html=True
    )

# Show retrieved context for RAG bot
if chatbot_type == "RAG Chatbot" and st.session_state.retrieved_context:
    st.markdown("**Retrieved Context:**")
    for doc in st.session_state.retrieved_context:
        st.markdown(f"<div class='context'>{doc}</div>", unsafe_allow_html=True)

# Download chat history
if st.button("Download Chat History"):
    download_text = "\n".join([f"{msg['role'].capitalize()} [{msg['timestamp']}]: {msg['content']}" for msg in conversation])
    st.download_button("Download", download_text, file_name=f"{chatbot_type.replace(' ','_')}_chat.txt")
