import streamlit as st
from src.service import SEOAnalyzerService
from src.models import Report
import pandas as pd

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


def main():
    st.set_page_config(page_title="SEO Analyzer", page_icon="🔍", layout="wide")
    st.markdown(custom_css, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="header-container">
            <div class="logo-container">
                <a href="https://www.nassim.com.br" target="_blank">
                    <img src="https://www.nassim.com.br/NassinAssets/NassinBrancoRemodel.png" alt="SEO Analyzer Logo" class="logo-default">
                    <img src="https://www.nassim.com.br/NassinAssets/NassinVermelhoRemodel.png" alt="SEO Analyzer Logo Hover" class="logo-hover">
                </a>
            </div>
            <div class="title-container">
                <h1>SEO Analyzer</h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "seo_service" not in st.session_state:
        st.session_state["seo_service"] = SEOAnalyzerService()

    url = st.text_input("Enter the website URL to analyze:")

    if st.button("Analyze"):
        if url:
            with st.spinner("Analyzing..."):
                report = st.session_state["seo_service"].analyze(url)
                st.session_state["report"] = report
                st.session_state["analysis_complete"] = True
        else:
            st.warning("Please enter a valid URL.")

    if st.session_state.get("analysis_complete", False):
        display_report(st.session_state["report"], st.session_state["seo_service"])
        st.write("---")
        if st.button("Generate Suggestions"):
            suggestions = st.session_state["seo_service"].generate_suggestions(
                st.session_state["report"]
            )
            st.session_state["suggestions"] = suggestions

    if "suggestions" in st.session_state:
        display_suggestions(st.session_state["suggestions"])


def display_report(report: Report, seo_service: SEOAnalyzerService):
    st.header("Overall Analysis Report")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-value">{len(report.pages)}</div>
                <div class="metric-label">Total pages analyzed</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-value">{report.total_time:.2f}s</div>
                <div class="metric-label">Total analysis time</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if report.errors:
            st.error(f"Errors encountered: {len(report.errors)}")
        if report.duplicate_pages:
            st.warning(f"Duplicate pages detected: {len(report.duplicate_pages)}")

    # Overall Keywords
    with st.expander("Overall Keywords", expanded=True):
        st.subheader("Top 10 Keywords")
        if report.keywords:
            df = pd.DataFrame(
                [(kw.word, kw.count) for kw in report.keywords[:10]],
                columns=["Keyword", "Count"],
            )
            df_transposed = df.set_index("Keyword").T
            st.table(
                df_transposed.style.hide(axis="index").set_properties(
                    **{"text-align": "left"}
                )
            )
        else:
            st.write("No keywords found.")

    # Pages Analysis
    st.subheader("Page Analysis")

    # Create multiple rows of tabs
    tabs_per_row = 20
    num_rows = (len(report.pages) + tabs_per_row - 1) // tabs_per_row

    for row in range(num_rows):
        cols = st.columns(tabs_per_row)
        for col, page_index in zip(
            cols,
            range(row * tabs_per_row, min((row + 1) * tabs_per_row, len(report.pages))),
        ):
            with col:
                page = report.pages[page_index]
                if st.button(f"Page {page_index + 1}", key=f"page_{page_index}"):
                    st.session_state["selected_page"] = page_index

    # Display selected page details
    if "selected_page" in st.session_state:
        page = report.pages[st.session_state["selected_page"]]
        st.write("---")
        st.subheader(f"Details for Page {st.session_state['selected_page'] + 1}")
        st.write(f"URL: {page.url}")
        st.write(f"Title: {page.title}")
        st.write(f"Description: {page.description}")
        st.write(f"Word Count: {page.word_count}")

        st.write("Top Keywords:")
        for count, word in page.keywords[:5]:
            st.write(f"- {word}: {count}")

        if page.warnings:
            st.write("Warnings:")
            for warning in page.warnings:
                st.write(f"- {warning}")

        # W3C Validation
        st.subheader("W3C Validation")
        if page.w3c_validation is None:
            if st.button("Validate Page"):
                with st.spinner("Validating page..."):
                    w3c_response = seo_service.validate_page(page.url)
                    page.w3c_validation = w3c_response
                st.rerun()
        else:
            w3c_results = page.w3c_validation
            st.write(f"Total messages: {len(w3c_results.messages)}")

            error_count = sum(1 for msg in w3c_results.messages if msg.type == "error")
            warning_count = sum(1 for msg in w3c_results.messages if msg.type == "info")

            st.write(f"Errors: {error_count}")
            st.write(f"Warnings: {warning_count}")

            with st.expander("View W3C Validation Details"):
                for msg in w3c_results.messages:
                    print(msg.type, msg.subtype)
                    match msg.type:
                        case "error":
                            st.error(f"Error: {msg.message}")
                        
                        case "info":
                            if msg.subtype != "warning":
                                st.info(f"Info: {msg.message}")
                            else:
                                st.warning(f"Warning: {msg.message}")
                        case _:
                            st.info(f"{msg.type.capitalize()}: {msg.message}")

                    if msg.first_column and msg.last_column:
                        st.write(
                            f"From line {msg.first_line}, column {msg.first_column}; to line {msg.last_line}, column {msg.last_column}"
                        )

                    if msg.extract:
                        st.code(msg.extract, language="html")

    # Errors
    if report.errors:
        with st.expander("Errors"):
            for error in report.errors:
                st.error(error)

    # Duplicate Pages
    if report.duplicate_pages:
        with st.expander("Duplicate Pages"):
            for i, duplicate_group in enumerate(report.duplicate_pages, 1):
                st.write(f"Group {i}: {', '.join(duplicate_group)}")


def display_suggestions(suggestions):
    st.header("SEO Suggestions")
    for category, category_suggestions in suggestions.items():
        with st.expander(category):
            for suggestion in category_suggestions:
                st.write(f"- {suggestion}")


if __name__ == "__main__":
    main()
