# SEO Analyzer

SEO Analyzer is a powerful tool designed to help you analyze and improve your website's search engine optimization (SEO). It provides detailed insights into various aspects of your website's SEO performance, including keyword analysis, page structure, and content quality.

## Features

- **Website Analysis**: Analyze any website by simply entering its URL.
- **Keyword Analysis**: Identify top keywords used across your website and on individual pages.
- **Page Structure Analysis**: Evaluate the structure of your web pages, including title and description lengths.
- **Content Quality Assessment**: Assess the quality of your content based on word count and other factors.
- **W3C Validation**: Validate your HTML against W3C standards to ensure compatibility and best practices.
- **Error and Warning Detection**: Identify potential SEO issues and receive suggestions for improvement.
- **PDF Report Generation**: Generate comprehensive PDF reports for easy sharing and offline analysis.
- **Interactive UI**: User-friendly interface built with Streamlit for easy navigation and data visualization.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/seo-analyzer.git
   cd seo-analyzer
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit app:
   ```
   streamlit run run.py
   ```

2. Open your web browser and navigate to the URL provided by Streamlit (usually `http://localhost:8501`).

3. Enter the URL of the website you want to analyze and click "Analyze".

4. Explore the various sections of the report, including overall analysis, page-specific details, and SEO suggestions.

5. Generate a PDF report for offline viewing or sharing by clicking the "Generate PDF Report" button.

## Project Structure

- `src/`: Contains the main source code for the project.
  - `ui/`: User interface components and Streamlit app configuration.
  - `models.py`: Data models for the project.
  - `service.py`: Core SEO analysis service.
  - `pdf_generator.py`: PDF report generation functionality.
- `run.py`: Entry point for running the Streamlit app.
- `requirements.txt`: List of Python dependencies.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Streamlit](https://streamlit.io/) for the amazing web app framework.
- [ReportLab](https://www.reportlab.com/) for PDF generation capabilities.
- [Plotly](https://plotly.com/) for interactive data visualizations.
