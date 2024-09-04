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
</style>
"""


def main():
    st.set_page_config(page_title="SEO Analyzer", page_icon="🔍", layout="wide")
    st.markdown(custom_css, unsafe_allow_html=True)

    # Custom header with logo and title
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

    # Create a single column for the form
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

    # Display report if analysis is complete
    if st.session_state.get("analysis_complete", False):
        display_report(st.session_state["report"])

        # Show "Generate Suggestions" button after the report
        if st.button("Generate Suggestions"):
            suggestions = st.session_state["seo_service"].generate_suggestions(
                st.session_state["report"]
            )
            st.session_state["suggestions"] = suggestions

    # Display suggestions if they exist
    if "suggestions" in st.session_state:
        display_suggestions(st.session_state["suggestions"])


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
