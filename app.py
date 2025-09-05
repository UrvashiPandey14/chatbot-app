import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables (for local testing)
load_dotenv()

# Get API key securely
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Use session_state for persistent chat history
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# Function to get response from Groq API
def get_groq_response():
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-versatile",  
        "messages": st.session_state.conversation_history
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

# Streamlit UI
st.title("💬 Chatbot with Conversation History")

user_message = st.text_input("You:", "")

if st.button("Send") and user_message.strip():
    # Add user message
    st.session_state.conversation_history.append({"role": "user", "content": user_message})

    # Get bot response
    bot_response = get_groq_response()
    st.session_state.conversation_history.append({"role": "assistant", "content": bot_response})

# Display conversation
for msg in st.session_state.conversation_history:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**Bot:** {msg['content']}")
