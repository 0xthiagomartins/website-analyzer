import streamlit as st

from src.pdf_generator import PDFGenerator
from src.service import SEOAnalyzerService
from src.url_safety import UnsafeUrlError, validate_public_url

from .components.header import header
from .components.report import ReportView
from .conf import configure

PDF_FILE_NAME = "seo_analysis_report.pdf"


def initialize_session_state():
    if "seo_service" not in st.session_state:
        st.session_state["seo_service"] = SEOAnalyzerService()
    if "analysis_complete" not in st.session_state:
        st.session_state["analysis_complete"] = False


def reset_analysis_state():
    for key in ("report", "suggestions", "selected_page", "pdf_data", "pdf_file_name"):
        st.session_state.pop(key, None)
    st.session_state["analysis_complete"] = False


def create_pdf_download():
    try:
        with st.spinner("Generating PDF report..."):
            pdf_data = PDFGenerator.generate_bytes(st.session_state["report"])
    except Exception as exc:
        st.session_state.pop("pdf_data", None)
        st.session_state.pop("pdf_file_name", None)
        st.error(f"Unable to generate the PDF report: {exc}")
    else:
        st.session_state["pdf_data"] = pdf_data
        st.session_state["pdf_file_name"] = PDF_FILE_NAME


def render_pdf_download_button():
    pdf_data = st.session_state.get("pdf_data")
    if pdf_data is None:
        return

    st.download_button(
        label="Download PDF Report",
        data=pdf_data,
        file_name=st.session_state.get("pdf_file_name", PDF_FILE_NAME),
        mime="application/pdf",
    )


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

        if st.button("Generate PDF Report"):
            create_pdf_download()

        render_pdf_download_button()

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
