import streamlit as st
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Initialize session state
if "conversation" not in st.session_state:
    st.session_state.conversation = []

if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# Dropdown to select chatbot type
chatbot_type = st.selectbox(
    "Choose a Chatbot:",
    ["Conversation History Bot", "No History Bot", "System Prompt Bot"]
)

def get_groq_response(messages):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages
    }
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            response_data = response.json()
            return response_data['choices'][0]['message']['content']
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

def handle_chat(user_message):
    timestamp = datetime.now().strftime("%H:%M:%S")

    if chatbot_type == "No History Bot":
        messages = [{"role": "user", "content": user_message}]
    elif chatbot_type == "System Prompt Bot":
        messages = [
            {"role": "system", "content": "You are a helpful assistant chatbot."},
            {"role": "user", "content": user_message}
        ]
    else:  # Conversation History Bot
        st.session_state.conversation.append({"role": "user", "content": user_message, "time": timestamp})
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.conversation if msg["role"] in ["user", "assistant"]]

    bot_response = get_groq_response(messages)
    st.session_state.conversation.append({"role": "assistant", "content": bot_response, "time": timestamp})

# --- UI ---
st.title("🤖 Multi-Mode Chatbot")

user_input = st.text_input("You:", value=st.session_state.user_input, key="user_input_input")

if st.button("Send"):
    if user_input.strip():
        handle_chat(user_input)
        # reset input safely
        st.session_state.user_input = ""
        st.experimental_rerun()  # refresh UI so input clears

# Display conversation
for msg in st.session_state.conversation:
    role = "🧑 You" if msg["role"] == "user" else "🤖 Bot"
    st.markdown(f"**{role} ({msg['time']}):** {msg['content']}")
