import streamlit as st


def header():
    st.markdown(
        """
        <div class="header-container">
            <div class="logo-container">
                <a href="https://www.nassim.com.br" target="_blank">
                    <img src="https://raw.githubusercontent.com/Nassim-Tecnologia/brand-assets/refs/heads/main/logo-marca-light-without-bg.png" alt="SEO Analyzer Logo" class="logo-default">
                    <img src="https://raw.githubusercontent.com/Nassim-Tecnologia/brand-assets/refs/heads/main/logo-marca-primary-without-bg.png" alt="SEO Analyzer Logo Hover" class="logo-hover">
                </a>
            </div>
            <div class="title-container">
                <h1>SEO Analyzer</h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
