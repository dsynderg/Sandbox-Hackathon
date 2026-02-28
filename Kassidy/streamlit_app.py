import streamlit as st
import os

st.set_page_config(page_title="My AI App", layout="wide")

# Check if we're running from the pages folder
if "pages" in os.path.abspath(__file__):
    st.stop()

# Custom CSS for button hover effect
st.markdown("""
    <style>
    /* Target Streamlit buttons */
    div.stButton > button:hover {
        background-color: #35e8d3 !important;
        border-color: #35e8d3 !important;
        color: #000000 !important;
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
    st.markdown("<h1 style='text-align: center;'>Tutor AI</h1>",
                unsafe_allow_html=True)

# Add more vertical spacing
st.write("")
st.write("")

# Create centered buttons in same column
col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    if st.button("Tutor", use_container_width=True, key="tutor_btn"):
        st.switch_page("pages/tutorBot.py")

    if st.button("Student", use_container_width=True, key="student_btn"):
        st.switch_page("pages/studentBot.py")

    if st.button("Quiz", use_container_width=True, key="quiz_btn"):
        st.switch_page("pages/quizGenerator.py")
