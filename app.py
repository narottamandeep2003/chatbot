import streamlit as st
from streamlit_javascript import st_javascript
import requests
from datetime import datetime

st.set_page_config(page_title="💬 ChatBot", layout="centered")
st.title("💬 ChatBot")

st.markdown("""
<style>
.stChatMessage {
    margin-bottom: -0.5rem;
    margin-top: -0.5rem;
    padding-bottom: 0.25rem;
    padding-top: 0.25rem;
}

.stChatMessage [data-testid="chatMessageContent"] {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
}

div[data-testid="stVerticalBlock"] > div > div:has(div.stChatMessage) {
    gap: 0px;
}

div[data-testid="stVerticalBlock"] > div > [data-testid="stVerticalBlock"] {
    gap: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

if "set_name" not in st.session_state:
    st.session_state.set_name = False

if "user_name" not in st.session_state:
    st.session_state.user_name = None

if "messages" not in st.session_state or not isinstance(st.session_state.messages, list):
    st.session_state.messages = []

current_user_name = st.session_state.user_name

if not current_user_name and not st.session_state.set_name:
    user_name_from_js = st_javascript("localStorage.getItem('username');")

    if user_name_from_js:
        st.session_state.user_name = user_name_from_js
        st.session_state.set_name = True
        st.rerun()
    else:
        st.session_state.set_name = False

current_user_name = st.session_state.user_name

if not current_user_name:
    if not st.session_state.messages:
        st.session_state.messages.append({"sender": "Bot", "type": "text", "content": "👋 Hello! What's your name?"})

    for msg_data in st.session_state.messages:
        if isinstance(msg_data, dict) and all(k in msg_data for k in ["sender", "type", "content"]):
            with st.chat_message(msg_data["sender"].lower()):
                if msg_data["type"] == "gif":
                    st.markdown(msg_data["content"], unsafe_allow_html=True)
                else:
                    st.write(msg_data["content"])
        else:
            st.warning(f"Skipping malformed message in history: {msg_data}")

    if name_prompt := st.chat_input("Enter your name here"):
        user_name_input = name_prompt.strip()

        if user_name_input:
            st_javascript(f"localStorage.setItem('username', '{user_name_input}');")
            st.session_state.user_name = user_name_input
            st.session_state.set_name = True

            st.session_state.messages.append({"sender": user_name_input, "type": "text", "content": user_name_input})
            st.session_state.messages.append({"sender": "Bot", "type": "text", "content": f"Nice to meet you, {user_name_input}! How can I help you today?"})
            st.rerun()
        else:
            st.session_state.messages.append({"sender": "Bot", "type": "text", "content": "Please enter a valid name."})
            st.rerun()

else:
    st.markdown(f"**Welcome back, `{current_user_name}`!** Start chatting below 👇")

    for msg_data in st.session_state.messages:
        if isinstance(msg_data, dict) and all(k in msg_data for k in ["sender", "type", "content"]):
            with st.chat_message(msg_data["sender"].lower()):
                if msg_data["type"] == "gif":
                    st.markdown(msg_data["content"], unsafe_allow_html=True)
                else:
                    st.write(msg_data["content"])
        else:
            st.warning(f"Skipping malformed message in history: {msg_data}")

    if prompt := st.chat_input("Type your message"):
        st.session_state.messages.append({"sender": current_user_name, "type": "text", "content": prompt})

        OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]

        url = 'https://openrouter.ai/api/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
        }

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        api_messages = []
        system_message_content = f"The user's name is {current_user_name}. The current date and time is {current_time}. Respond to the user's queries."
        api_messages.append({"role": "system", "content": system_message_content})

        for msg in st.session_state.messages:
            if msg["type"] == "text":
                if msg["sender"] == current_user_name:
                    role = "user"
                elif msg["sender"] == "Bot":
                    role = "assistant"
                else:
                    role = "user"

                api_messages.append({"role": role, "content": msg["content"]})
        
        payload = {
            'model': 'mistralai/mistral-7b-instruct',
            'messages': api_messages,
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data and data['choices'] and data['choices'][0]['message']['content']:
                bot_response_content = data['choices'][0]['message']['content']
                st.session_state.messages.append({"sender": "Bot", "type": "text", "content": bot_response_content})
            else:
                st.session_state.messages.append({"sender": "Bot", "type": "text", "content": "Error: Could not get a valid response from the API."})

        except requests.exceptions.RequestException as e:
            st.error(f"API Request failed: {e}")
            st.session_state.messages.append({"sender": "Bot", "type": "text", "content": f"Sorry, there was an error connecting to the AI: {e}"})
        
        st.rerun()