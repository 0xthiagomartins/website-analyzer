import streamlit as st
from src.service import SEOAnalyzerService
from src.pdf_generator import PDFGenerator
from src.url_safety import UnsafeUrlError, validate_public_url
import os
from .components.header import header
from .conf import configure
from .components.report import ReportView


def initialize_session_state():
    if "seo_service" not in st.session_state:
        st.session_state["seo_service"] = SEOAnalyzerService()
    if "analysis_complete" not in st.session_state:
        st.session_state["analysis_complete"] = False


def reset_analysis_state():
    for key in ("report", "suggestions", "selected_page"):
        st.session_state.pop(key, None)
    st.session_state["analysis_complete"] = False


def main():
    configure()
    initialize_session_state()
    header()

    url = st.text_input("Enter the website URL to analyze:")

    if st.button("Analyze"):
        reset_analysis_state()
        if not url:
            st.warning("Please enter a valid URL.")
        else:
            try:
                safe_url = validate_public_url(url)
            except UnsafeUrlError as exc:
                st.warning(str(exc))
            else:
                try:
                    with st.spinner("Analyzing..."):
                        report = st.session_state["seo_service"].analyze(safe_url)
                except Exception as exc:
                    st.error(f"Unable to analyze the URL: {exc}")
                else:
                    st.session_state["report"] = report
                    st.session_state["analysis_complete"] = True

    if st.session_state.get("analysis_complete", False):
        ReportView()
        st.write("---")
        if st.button("Generate Suggestions"):
            suggestions = st.session_state["seo_service"].generate_suggestions(
                st.session_state["report"]
            )
            st.session_state["suggestions"] = suggestions

        # Add a button to generate PDF report
        if st.button("Generate PDF Report"):
            pdf_file = "seo_analysis_report.pdf"
            try:
                with st.spinner("Generating PDF report..."):
                    pdf_generator = PDFGenerator(st.session_state["report"], pdf_file)
                    pdf_generator.generate()
            except Exception as exc:
                st.error(f"Unable to generate the PDF report: {exc}")
            else:
                with open(pdf_file, "rb") as file:
                    st.download_button(
                        label="Download PDF Report",
                        data=file,
                        file_name=pdf_file,
                        mime="application/pdf",
                    )
                os.remove(pdf_file)

    if "suggestions" in st.session_state:
        display_suggestions(st.session_state["suggestions"])


def display_suggestions(suggestions):
    st.header("SEO Suggestions")
    for category, category_suggestions in suggestions.items():
        with st.expander(category):
            for suggestion in category_suggestions:
                st.write(f"- {suggestion}")


if __name__ == "__main__":
    main()
