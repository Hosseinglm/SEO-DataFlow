import streamlit as st

def apply_theme(theme):
    """Apply custom theme settings"""
    if theme == 'dark':
        st.markdown("""
            <style>
            .stApp {
                background-color: #0E1117;
                color: #FAFAFA;
            }
            .stButton>button {
                color: #FAFAFA;
                background-color: #FF4B4B;
                border: none;
            }
            .stTextInput>div>div>input {
                color: #FAFAFA;
                background-color: #262730;
            }
            </style>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            .stApp {
                background-color: #FFFFFF;
                color: #000000;
            }
            .stButton>button {
                color: #FFFFFF;
                background-color: #FF4B4B;
                border: none;
            }
            .stTextInput>div>div>input {
                color: #000000;
                background-color: #F0F2F6;
            }
            </style>
            """, unsafe_allow_html=True)
