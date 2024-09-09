import streamlit as st
from src.service import SEOAnalyzerService
from src.models import Report
import pandas as pd
from src.pdf_generator import PDFGenerator
import os
import plotly.express as px

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

        # Add a button to generate PDF report
        if st.button("Generate PDF Report"):
            pdf_file = "seo_analysis_report.pdf"
            with st.spinner("Generating PDF report..."):
                pdf_generator = PDFGenerator(st.session_state["report"], pdf_file)
                pdf_generator.generate()

            # Provide a download link for the generated PDF
            with open(pdf_file, "rb") as file:
                btn = st.download_button(
                    label="Download PDF Report",
                    data=file,
                    file_name=pdf_file,
                    mime="application/pdf",
                )

            # Optionally, remove the file after providing the download link
            os.remove(pdf_file)

    if "suggestions" in st.session_state:
        display_suggestions(st.session_state["suggestions"])


def render_page_overview(report):
    st.subheader("Page Analysis Overview")

    # Prepare data for the overview table
    overview_data = []
    for page in report.pages:
        overview_data.append(
            {
                "URL": page.url,
                "Title Length": len(page.title),
                "Description Length": len(page.description),
                "Word Count": page.word_count,
                "Warnings": len(page.warnings),
            }
        )

    overview_df = pd.DataFrame(overview_data)

    # Display the overview table with conditional formatting
    st.dataframe(
        overview_df.style.background_gradient(
            subset=["Title Length", "Description Length", "Word Count"], cmap="RdYlGn"
        )
        .highlight_between(
            subset=["Title Length"], left=30, right=60, color="lightgreen"
        )
        .highlight_between(
            subset=["Description Length"], left=50, right=160, color="lightgreen"
        )
        .highlight_between(
            subset=["Word Count"], left=300, right=float("inf"), color="lightgreen"
        )
        .highlight_between(
            subset=["Warnings"], left=1, right=float("inf"), color="yellow"
        )
    )


def render_page_details(report, seo_service):
    st.subheader("Detailed Page Analysis")

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
                if st.button(f"{page_index + 1:03d}", key=f"page_{page_index}"):
                    st.session_state["selected_page"] = page_index

    # Display selected page details
    if "selected_page" in st.session_state:
        page = report.pages[st.session_state["selected_page"]]
        st.write("---")
        st.subheader(f"Details for Page {st.session_state['selected_page'] + 1}")

        # Create three columns for main page info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Word Count", page.word_count)
        with col2:
            st.metric("Title Length", len(page.title))
        with col3:
            st.metric("Description Length", len(page.description))

        # URL
        st.markdown(f"**URL:** [{page.url}]({page.url})")

        # Title and Description
        with st.expander("Title and Description", expanded=True):
            st.markdown(f"**Title:** {page.title}")
            st.markdown(f"**Description:** {page.description}")

        # Top Keywords
        with st.expander("Top Keywords", expanded=True):
            keyword_data = pd.DataFrame(
                page.keywords[:10], columns=["Count", "Keyword"]
            )
            st.bar_chart(keyword_data.set_index("Keyword"))

        # Warnings
        render_warnings(page.warnings)

        # W3C Validation
        render_w3c_validation(page, seo_service)


def display_report(report: Report, seo_service: SEOAnalyzerService):
    render_overall_overview(report)

    render_page_overview(report)

    render_page_details(report, seo_service)

    render_errors(report.errors)

    # Add a back button
    if st.button("Back to Overview"):
        del st.session_state["selected_page"]
        st.rerun()


def render_overall_overview(report):
    st.header("Overall Analysis Report")

    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Pages", len(report.pages))
    with col2:
        st.metric("Analysis Time", f"{report.total_time:.2f}s")
    with col3:
        st.metric("Errors", len(report.errors) if report.errors else 0)
    with col4:
        st.metric(
            "Duplicate Pages",
            len(report.duplicate_pages) if report.duplicate_pages else 0,
        )

    # Overall Keywords
    with st.expander("Overall Keywords", expanded=True):
        st.subheader("Top 10 Keywords")
        if report.keywords:
            df = pd.DataFrame(
                [(kw.word, kw.count) for kw in report.keywords[:10]],
                columns=["Keyword", "Count"],
            )
            fig = px.bar(df, x="Keyword", y="Count", title="Top 10 Keywords")
            fig.update_layout(xaxis_title="Keyword", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No keywords found.")

    # Duplicate Pages
    if report.duplicate_pages:
        with st.expander("Duplicate Pages", expanded=True):
            for i, duplicate_group in enumerate(report.duplicate_pages, 1):
                st.markdown(f"**Group {i}:**")
                for url in duplicate_group:
                    st.markdown(f"- [{url}]({url})")
                st.markdown("---")

    # Error Summary
    if report.errors:
        with st.expander("Error Summary", expanded=True):
            error_df = pd.DataFrame(report.errors, columns=["Error"])
            error_counts = error_df["Error"].value_counts().reset_index()
            error_counts.columns = ["Error", "Count"]
            fig = px.pie(
                error_counts, values="Count", names="Error", title="Error Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)


def render_warnings(warnings):
    if warnings:
        with st.expander("Warnings", expanded=False):
            for warning in warnings:
                st.warning(warning)


def render_errors(errors):
    if errors:
        with st.expander("Errors", expanded=True):
            for error in errors:
                st.error(error)


def render_w3c_validation(page, seo_service):
    st.subheader("W3C Validation")
    if page.w3c_validation is None:
        if st.button("Validate Page"):
            with st.spinner("Validating page..."):
                w3c_response = seo_service.validate_page(page.url)
                page.w3c_validation = w3c_response
            st.rerun()
    else:
        w3c_results = page.w3c_validation
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Messages", len(w3c_results.messages))
        with col2:
            st.metric(
                "Errors",
                sum(1 for msg in w3c_results.messages if msg.type == "error"),
            )
        with col3:
            st.metric(
                "Warnings",
                sum(1 for msg in w3c_results.messages if msg.type == "info"),
            )

        with st.expander("W3C Validation Details"):
            for msg in w3c_results.messages:
                if msg.type == "error":
                    st.error(f"Error: {msg.message}")
                elif msg.type == "info":
                    st.warning(f"Warning: {msg.message}")
                else:
                    st.info(f"Info: {msg.message}")

                if (
                    msg.first_line
                    and msg.first_column
                    and msg.last_line
                    and msg.last_column
                ):
                    st.text(
                        f"From line {msg.first_line}, column {msg.first_column}; to line {msg.last_line}, column {msg.last_column}"
                    )

                if msg.extract:
                    st.code(msg.extract, language="html")

                st.markdown("---")


def display_suggestions(suggestions):
    st.header("SEO Suggestions")
    for category, category_suggestions in suggestions.items():
        with st.expander(category):
            for suggestion in category_suggestions:
                st.write(f"- {suggestion}")


if __name__ == "__main__":
    main()
