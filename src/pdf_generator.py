from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from datetime import datetime
from src.models import Report
import requests
from io import BytesIO


class PDFGenerator:
    def __init__(self, report: Report, filename: str):
        self.report = report
        self.filename = filename
        self.doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        self.styles = getSampleStyleSheet()
        self.elements = []
        self.logo_url = "https://www.nassim.com.br/NassinAssets/NassinBrancoRemodel.png"
        self.logo_image = self._get_logo()

        # Define custom colors
        self.primary_color = colors.HexColor("#D33F49")
        self.background_color = colors.HexColor("#F0F0F0")
        self.text_color = colors.HexColor("#04080F")

        # Update styles
        self._update_styles()

    def _get_logo(self):
        response = requests.get(self.logo_url)
        return Image(BytesIO(response.content), width=1.5 * inch, height=0.5 * inch)

    def _update_styles(self):
        for style in self.styles.byName.values():
            style.textColor = self.text_color
            style.backColor = self.background_color

        self.styles.add(
            ParagraphStyle(
                name="Footer",
                parent=self.styles["Normal"],
                textColor=colors.black,
                backColor=self.primary_color,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            )
        )

    def _header_footer(self, canvas, doc):
        canvas.saveState()

        # Header
        header_height = 54
        canvas.setFillColor(self.primary_color)
        canvas.rect(0, A4[1] - header_height, A4[0], header_height, fill=1)

        # Center the logo vertically in the header
        logo_y = A4[1] - header_height / 2 - self.logo_image.drawHeight / 2
        self.logo_image.drawOn(canvas, 72 + 10, logo_y)

        # Set up the "SEO Analysis Report" text
        font_size = 18
        canvas.setFont("Helvetica-Bold", font_size)
        canvas.setFillColor(colors.white)
        text = "SEO Analysis Report"
        text_width = canvas.stringWidth(text, "Helvetica-Bold", font_size)
        x = (A4[0] - text_width) / 2  # Center the text horizontally
        y = A4[1] - (header_height / 2) + (font_size / 3)  # Adjust vertical position
        canvas.drawString(x, y, text)

        # Footer (unchanged)
        footer_height = 54
        canvas.setFillColor(self.primary_color)
        canvas.rect(0, 0, A4[0], footer_height, fill=1)
        canvas.setFillColor(colors.black)
        # Center the logo vertically in the footer
        logo_y = footer_height / 2 - self.logo_image.drawHeight / 2
        self.logo_image.drawOn(canvas, 72 + 10, logo_y)

        # Add the page number to the right side of the footer
        canvas.setFont("Helvetica-Bold", 9)  # Reset font for footer
        canvas.drawRightString(A4[0] - 72, footer_height / 2, str(doc.page))

        # Move the generation date to the left side
        canvas.drawString(
            72 + 1.5 * inch + 20,
            footer_height / 2,
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        )

        canvas.restoreState()

    def _create_title(self, text, style="Heading1"):
        self.elements.append(Paragraph(text, self.styles[style]))
        self.elements.append(Spacer(1, 12))

    def _create_paragraph(self, text, style="BodyText"):
        self.elements.append(Paragraph(text, self.styles[style]))
        self.elements.append(Spacer(1, 12))

    def _create_table(self, data, colWidths=None):
        table = Table(data, colWidths=colWidths)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.primary_color),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 14),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), self.background_color),
                    ("TEXTCOLOR", (0, 1), (-1, -1), self.text_color),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 12),
                    ("TOPPADDING", (0, 1), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 1, self.text_color),
                ]
            )
        )
        self.elements.append(table)
        self.elements.append(Spacer(1, 12))

    def generate(self):
        self._create_title("SEO Analysis Technical Report")

        self._create_paragraph(
            "This report provides a comprehensive analysis of the SEO performance for the analyzed website."
        )

        self._create_title("1. Overview", "Heading2")
        self._create_paragraph(f"Total pages analyzed: {len(self.report.pages)}")
        self._create_paragraph(
            f"Total analysis time: {self.report.total_time:.2f} seconds"
        )

        self._create_title("2. Keywords", "Heading2")
        keyword_data = [["Keyword", "Count"]] + [
            [kw.word, kw.count] for kw in self.report.keywords[:10]
        ]
        self._create_table(keyword_data)

        self._create_title("3. Page Analysis", "Heading2")
        for i, page in enumerate(self.report.pages, 1):
            self._create_title(f"3.{i}. {page.url}", "Heading3")
            self._create_paragraph(f"Title: {page.title}")
            self._create_paragraph(f"Description: {page.description}")
            self._create_paragraph(f"Word Count: {page.word_count}")

            if page.warnings:
                self._create_paragraph("Warnings:")
                for warning in page.warnings:
                    self._create_paragraph(f"- {warning}", "BodyText")

            if i < len(self.report.pages):
                self.elements.append(PageBreak())

        def page_canvas(canvas, doc):
            canvas.saveState()
            canvas.setFillColor(self.background_color)
            canvas.rect(0, 0, A4[0], A4[1], fill=1)
            self._header_footer(canvas, doc)
            canvas.restoreState()

        self.doc.build(
            self.elements,
            onFirstPage=page_canvas,
            onLaterPages=page_canvas,
        )
