import streamlit as st
from src.service import SEOAnalyzerService
from src.pdf_generator import PDFGenerator
import os
from .components.header import header
from .conf import configure
from .components.report import Report


def initialize_session_state():
    if "seo_service" not in st.session_state:
        st.session_state["seo_service"] = SEOAnalyzerService()


def main():
    configure()
    initialize_session_state()
    header()

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
        Report()
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
