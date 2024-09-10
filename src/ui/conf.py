import streamlit as st


custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

    :root {
        --primary: #D33F49;
        --black: #04080F;
        --white: #FBFFFE;
        --neutral: #A0A0A0;
    }

    body {
        font-family: 'JetBrains Mono', monospace;
        background-color: var(--black);
        color: var(--white);
    }

    .stButton > button {
        background-color: var(--primary);
        color: var(--white);
    }

    .stTextInput > div > div > input {
        background-color: var(--neutral);
        color: var(--black);
    }

    .stExpander {
        border-color: var(--primary);
    }

    .stTab {
        background-color: var(--neutral);
        color: var(--black);
    }

    .stTab[aria-selected="true"] {
        background-color: var(--primary);
        color: var(--white);
    }

    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0;
    }

    .logo-container {
        width: 200px;  /* Adjust this value as needed */
    }

    .logo-container img {
        max-width: 100%;
        height: auto;
        transition: opacity 0.3s ease;
    }

    .logo-container .logo-hover {
        display: none;
    }

    .logo-container:hover .logo-default {
        display: none;
    }

    .logo-container:hover .logo-hover {
        display: inline;
    }

    .title-container {
        flex-grow: 1;
        text-align: center;
    }

    .metric-container {
        background-color: transparent;
        border: 1px solid var(--primary);
        border-radius: 5px;
        padding: 10px;
        text-align: center;
    }

    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: var(--primary);
    }

    .metric-label {
        font-size: 18px;
        color: var(--white);
    }
</style>
"""


def configure():
    st.set_page_config(page_title="SEO Analyzer", page_icon="🔍", layout="wide")
    st.markdown(custom_css, unsafe_allow_html=True)
