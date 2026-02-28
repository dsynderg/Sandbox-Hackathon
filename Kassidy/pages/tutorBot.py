import os
import streamlit as st
from openai import OpenAI
from pathlib import Path

# Add back button at the top
if st.button("← Back to Home", key="back_tutor"):
    st.switch_page("streamlit_app.py")

st.title("🤖 Teacher Chatbot")

# Custom CSS for user icon color
st.markdown("""
    <style>
    /* Change user chat icon color */
    [data-testid="stChatMessageAvatarUser"] {
        background-color: #35e8d3 !important;
    }
    /* Change bot/assistant chat icon color - even lighter */
    [data-testid="stChatMessageAvatarAssistant"] {
        background-color: #8ff2e3 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Add MathJax for LaTeX rendering
mathjax_script = """
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
    <script>
    MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]'], ['[', ']']],
        processEscapes: true
      },
      svg: {
        fontCache: 'global'
      },
      startup: {
        pageReady: async () => {
          await MathJax.typesetPromise();
          const observer = new MutationObserver(async (mutations) => {
            await MathJax.typesetPromise();
          });
          observer.observe(document.body, { childList: true, subtree: true });
          return MathJax.startup.defaultPageReady();
        }
      }
    };
    </script>
    """
st.markdown(mathjax_script, unsafe_allow_html=True)

# Load system prompt from hardcoded markdown file path
try:
    # Get the project root by going up from current file location
    current_dir = Path(__file__).parent.parent.parent
    tutor_md_path = current_dir / "Dexter" / "Teacher_prompt.md"
    system_prompt = tutor_md_path.read_text(encoding="utf-8")
except Exception as e:
    system_prompt = ""
    st.warning(f"Could not load system prompt: {e}")

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

# Initialize chat history (tutor page)
if "tutor_messages" not in st.session_state:
    st.session_state.tutor_messages = []

# Display chat messages from history on app rerun
# Note: st.markdown() supports LaTeX! Use $...$ for inline math and $$...$$ for block math
for message in st.session_state.tutor_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a Question!"):
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
