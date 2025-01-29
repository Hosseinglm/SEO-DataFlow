import pandas as pd
import streamlit as st


def validate_seo_data(data):
    """Validate SEO data input"""
    required_fields = ['url', 'title', 'meta_description', 'h1_tags', 'keywords', 'page_rank']

    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"

    try:
        float(data['page_rank'])
    except ValueError:
        return False, "Page rank must be a number"

    return True, "Data is valid"


def format_date(date):
    """Format datetime for display"""
    return date.strftime("%Y-%m-%d %H:%M:%S")


def get_theme_toggle():
    """Handle dark/light theme toggle"""
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'

    theme = st.sidebar.radio(
        "Choose Theme",
        ('Dark', 'Light'),
        index=0 if st.session_state.theme == 'dark' else 1
    )

    st.session_state.theme = theme.lower()
    return st.session_state.theme
