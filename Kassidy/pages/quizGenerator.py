import os
import streamlit as st
from openai import OpenAI

# Add back button at the top
if st.button("← Back to Home"):
    st.switch_page("streamlit_app.py")

st.title("Quiz Generator")

# Get API key from session state (user input) only, or fall back to environment/secrets for local dev
API_KEY = st.session_state.get("user_api_key", None)
if not API_KEY:
    # Try environment/secrets as fallback (for local development)
    API_KEY = os.getenv("OPENAI_API_KEY") or st.secrets.get(
        "OPENAI_API_KEY", None)

if not API_KEY:
    st.error(
        "⚠️ Missing OpenAI API key. Please go back to the home page and enter your API key.")
    if st.button("← Back to Home"):
        st.switch_page("streamlit_app.py")
    st.stop()

client = OpenAI(api_key=API_KEY)

# Initialize chat history (student page)
if "quiz_messages" not in st.session_state:
    st.session_state.quiz_messages = []

# Display chat messages from history on app rerun
for message in st.session_state.quiz_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What is on your mind?"):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to history
    st.session_state.quiz_messages.append(
        {"role": "user", "content": prompt})

    # call OpenAI to get a response
    try:
        result = client.responses.create(
            model="gpt-4.1-nano",
            input=prompt,
        )
        response = result.output_text
    except Exception as e:
        response = f"Error contacting OpenAI: {e}"

    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.quiz_messages.append(
        {"role": "assistant", "content": response})
