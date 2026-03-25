import streamlit as st


def render_trusted_html(markup: str) -> None:
    """Render static, hardcoded markup only. Never pass user-controlled content."""

    st.markdown(markup, unsafe_allow_html=True)
