import streamlit as st
from src.service import SEOAnalyzerService
from src.models import Report

custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

    :root {
        --primary: #D33F49;
        --black: #04080F;
        --white: #FBFFFE;
        --neutral: #BABCC3;
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
</style>
"""


def main():
    st.set_page_config(page_title="SEO Analyzer", page_icon="🔍", layout="wide")
    st.markdown(custom_css, unsafe_allow_html=True)

    st.title("SEO Analyzer")

    # Initialize SEOAnalyzerService
    if "seo_service" not in st.session_state:
        st.session_state["seo_service"] = SEOAnalyzerService()

    url = st.text_input("Enter the website URL to analyze:")

    if st.button("Analyze"):
        if url:
            with st.spinner("Analyzing..."):
                report = st.session_state["seo_service"].analyze(url)
                st.session_state["report"] = report
                display_report(report)
                st.session_state["analysis_complete"] = True
        else:
            st.warning("Please enter a valid URL.")

    # Show "Generate Suggestions" button only after analysis is complete
    if st.session_state.get("analysis_complete", False):
        if st.button("Generate Suggestions"):
            suggestions = st.session_state["seo_service"].generate_suggestions(
                st.session_state["report"]
            )
            display_suggestions(suggestions)


def display_report(report: Report):
    st.header("Analysis Report")

    # Summary
    with st.expander("Summary", expanded=True):
        st.write(f"Total pages analyzed: {len(report.pages)}")
        st.write(f"Total analysis time: {report.total_time:.2f} seconds")
        if report.errors:
            st.error(f"Errors encountered: {len(report.errors)}")
        if report.duplicate_pages:
            st.warning(f"Duplicate pages detected: {len(report.duplicate_pages)}")

    # Overall Keywords
    with st.expander("Overall Keywords"):
        st.subheader("Top 10 Keywords")
        for keyword in report.keywords[:10]:
            st.write(f"- {keyword.word}: {keyword.count}")

    # Pages Analysis
    st.subheader("Page Analysis")
    tabs = st.tabs([f"Page {i+1}" for i in range(len(report.pages))])
    for i, (tab, page) in enumerate(zip(tabs, report.pages)):
        with tab:
            st.write(f"URL: {page.url}")
            st.write(f"Title: {page.title}")
            st.write(f"Description: {page.description}")
            st.write(f"Word Count: {page.word_count}")

            with st.expander("Top Keywords"):
                for count, word in page.keywords[:5]:
                    st.write(f"- {word}: {count}")

            if page.warnings:
                with st.expander("Warnings"):
                    for warning in page.warnings:
                        st.write(f"- {warning}")

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
