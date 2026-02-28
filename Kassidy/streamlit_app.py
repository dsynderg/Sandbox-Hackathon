import streamlit as st
import os

st.set_page_config(page_title="My AI App", layout="wide")

# Check if we're running from the pages folder
if "pages" in os.path.abspath(__file__):
    st.stop()

# Custom CSS for buttons and other elements
st.markdown("""
    <style>
    /* Apply Times New Roman to all buttons */
    button {
        font-family: "Times New Roman", Times, serif !important;
    }
    /* Apply Times New Roman to text inputs */
    input {
        font-family: "Times New Roman", Times, serif !important;
    }
    /* Style main navigation buttons - lighter than background */
    div.stButton > button[kind="primary"],
    div.stButton > button {
        background-color: #26b8bd !important;
        border-color: #26b8bd !important;
    }
    /* Hover effect - grayer version */
    div.stButton > button:hover {
        background-color: #4a9fa4 !important;
        border-color: #4a9fa4 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Add vertical spacing to center buttons
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")

# Create centered column layout
col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    st.markdown("<h1 style='text-align: center; font-family: \"Times New Roman\", Times, serif;'>Textbook AI</h1>",
                unsafe_allow_html=True)

# Add more vertical spacing
st.write("")
st.write("")

# Create centered buttons
col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    if st.button("Teacher", use_container_width=True, key="tutor_btn"):
        st.switch_page("pages/tutorBot.py")

    if st.button("Student", use_container_width=True, key="student_btn"):
        st.switch_page("pages/studentBot.py")

    if st.button("Quiz", use_container_width=True, key="quiz_btn"):
        st.switch_page("pages/quizGenerator.py")

# Add spacing before API key input
st.write("")
st.write("")

# API Key input field
col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    # Check if API key is already saved in session state
    if "user_api_key" not in st.session_state or not st.session_state.user_api_key:
        # Show input field if no API key is saved
        api_key_input = st.text_input(
            "Enter your OpenAI API Key:",
            type="password",
            placeholder="sk-...",
            help="Your API key will only be stored for this session",
            key="api_input"
        )

        # Button to save the API key
        if st.button("Save API Key", use_container_width=True):
            if api_key_input and api_key_input.startswith("sk-"):
                st.session_state.user_api_key = api_key_input
                st.rerun()  # Refresh to hide the input field
            else:
                st.error("Please enter a valid OpenAI API key (starts with 'sk-')")
    else:
        # Show confirmation message when key is saved
        st.success("✓ API Key saved for this session")
        if st.button("Clear API Key", use_container_width=True):
            del st.session_state.user_api_key
            st.rerun()
