import os
import streamlit as st
from openai import OpenAI
from pathlib import Path

# Add back button at the top
if st.button("← Back to Home", key="back_tutor"):
    st.switch_page("streamlit_app.py")

st.title("🤖 Tutor Chatbot")

# Load system prompt from hardcoded markdown file path
try:
    system_prompt = Path("../../Dexter/Tutor.md").read_text(encoding="utf-8")
except Exception as e:
    system_prompt = ""
    st.warning(f"Could not load system prompt: {e}")

# initialize OpenAI client using environment variable or Streamlit secrets
API_KEY = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
if not API_KEY:
    st.error(
        "Missing OpenAI API key. Set OPENAI_API_KEY in your environment or secrets.toml")
    st.stop()

client = OpenAI(api_key=API_KEY)

# Initialize chat history (tutor page)
if "tutor_messages" not in st.session_state:
    st.session_state.tutor_messages = []

# Display chat messages from history on app rerun
for message in st.session_state.tutor_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What is on your mind?"):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to history
    st.session_state.tutor_messages.append({"role": "user", "content": prompt})

    # call OpenAI to get a response
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(st.session_state.tutor_messages)
        
        result = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        response = result.choices[0].message.content
    except Exception as e:
        response = f"Error contacting OpenAI: {e}"

    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.tutor_messages.append(
        {"role": "assistant", "content": response})
