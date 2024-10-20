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
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from datetime import datetime
from src.models import Report
import requests
from io import BytesIO
import re
from html import escape
import matplotlib.pyplot as plt
import io


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
        self.logo_url = "https://raw.githubusercontent.com/Nassim-Tecnologia/brand-assets/refs/heads/main/logo-marca-light-without-bg.png"
        self.cover_logo_url = "https://raw.githubusercontent.com/Nassim-Tecnologia/brand-assets/refs/heads/main/logo-marca-dark-without-bg.png"
        self.logo_image = self._get_logo(self.logo_url)
        self.cover_logo_image = self._get_logo(self.cover_logo_url)

        # Define custom colors
        self.primary_color = colors.Color(red=0.827, green=0.247, blue=0.286)  # #D33F49
        self.background_color = colors.HexColor("#FBFFFE")
        self.text_color = colors.HexColor("#04080F")

        # Update styles
        self._update_styles()

    def _get_logo(self, url, width=1.5 * inch, height=0.5 * inch):
        response = requests.get(url)
        return Image(BytesIO(response.content), width=width, height=height)

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

        # Add Subtitle style
        self.styles.add(
            ParagraphStyle(
                name="Subtitle",
                parent=self.styles["Normal"],
                fontSize=14,
                leading=16,
                textColor=self.text_color,
                alignment=TA_CENTER,
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
        y = (
            -12.5 + A4[1] - (header_height / 2) + (font_size / 3)
        )  # Adjust vertical position
        canvas.drawString(x, y, text)

        # Footer
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
        # Remove HTML-like tags
        cleaned_text = re.sub(r"<[^>]+>", "", text)
        # Escape any remaining special characters
        escaped_text = escape(cleaned_text)
        self.elements.append(Paragraph(escaped_text, self.styles[style]))
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

    def _create_cover_page(self):
        # Use the cover logo image with increased size
        cover_logo = self._get_logo(
            self.cover_logo_url, width=3.75 * inch, height=1.25 * inch
        )
        self.elements.append(Spacer(1, 30))  # Increased spacing
        self.elements.append(cover_logo)
        self.elements.append(Spacer(1, 80))  # Increased spacing

        # Title
        title_style = ParagraphStyle(
            name="CoverTitle",
            parent=self.styles["Title"],
            fontSize=24,
            leading=28,
            alignment=TA_CENTER,
        )
        self.elements.append(Paragraph("SEO Analysis Report", title_style))
        self.elements.append(Spacer(1, 50))  # Increased spacing

        # Subtitle
        self.elements.append(Paragraph(f"Analysis for:", self.styles["Subtitle"]))
        self.elements.append(
            Paragraph(f"{self.report.pages[0].url[8:]}", self.styles["Subtitle"])
        )
        self.elements.append(Spacer(1, 100))  # Increased spacing

        # Year (bigger and bold)
        year_style = ParagraphStyle(
            name="YearStyle",
            parent=self.styles["Normal"],
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )
        self.elements.append(Paragraph(f"{datetime.now().year}", year_style))
        self.elements.append(Spacer(1, 80))  # Increased spacing

        # Short description (30% width and justified)
        desc_style = ParagraphStyle(
            name="DescriptionStyle",
            parent=self.styles["Normal"],
            alignment=TA_JUSTIFY,
        )
        description = (
            "This report provides a comprehensive analysis of the SEO performance for the analyzed website, "
            "including keyword analysis, page-by-page breakdown, and actionable insights."
        )

        # Create a table to control the width of the description
        desc_table = Table(
            [[Paragraph(description, desc_style)]], colWidths=[0.3 * self.doc.width]
        )
        self.elements.append(desc_table)

    def _create_summary_page(self):
        summary_elements = []
        summary_elements.append(Paragraph("Table of Contents", self.styles["Heading1"]))
        summary_elements.append(Spacer(1, 20))

        summary_style = ParagraphStyle(
            name="SummaryItem",
            parent=self.styles["Normal"],
            firstLineIndent=0,
            alignment=TA_LEFT,
        )

        indented_summary_style = ParagraphStyle(
            name="IndentedSummaryItem",
            parent=summary_style,
            leftIndent=20,
        )

        # Find the correct page numbers
        overview_page = self._find_page_number("1. Overview")
        keywords_page = self._find_page_number("2. Keywords")
        page_analysis_start = self._find_page_number("3. Page Analysis")

        # Add summary items with correct page numbers
        self._add_summary_item(
            "1. Overview", overview_page, summary_style, summary_elements
        )
        self._add_summary_item(
            "2. Keywords", keywords_page, summary_style, summary_elements
        )
        self._add_summary_item(
            "3. Page Analysis", page_analysis_start, summary_style, summary_elements
        )

        # Add subtitles for Page Analysis
        for i, page in enumerate(self.report.pages, 1):
            page_number = self._find_page_number(f"3.{i}. {page.url}")
            self._add_summary_item(
                f"3.{i}. {page.url}",
                page_number,
                indented_summary_style,
                summary_elements,
            )

        return summary_elements

    def _find_page_number(self, title):
        for i, element in enumerate(self.elements):
            if isinstance(element, Paragraph) and element.text == title:
                return (i // 45) + 3  # Approximate number of elements per page
        return None

    def _add_summary_item(self, text, page, style, elements):
        if page is not None:
            item_text = f"{text} {'.' * (70 - len(text) - len(str(page)))} {page}"
            elements.append(Paragraph(item_text, style))
            elements.append(Spacer(1, 5))

    def generate(self):
        # Create cover page (no header/footer)
        self._create_cover_page()

        # Create a placeholder for the summary page
        self.elements.append(PageBreak())
        summary_placeholder = PageBreak()
        self.elements.append(summary_placeholder)
        self.elements.append(PageBreak())

        # Generate the rest of the content
        self._generate_content()

        # Create the summary page with accurate page numbers
        summary_elements = self._create_summary_page()

        # Insert the summary page at the correct position
        summary_index = self.elements.index(summary_placeholder)
        self.elements[summary_index : summary_index + 1] = summary_elements

        def first_page(canvas, doc):
            # No header/footer for the first page (cover)
            canvas.saveState()
            canvas.setFillColor(self.background_color)
            canvas.rect(0, 0, A4[0], A4[1], fill=1)
            canvas.restoreState()

        def later_pages(canvas, doc):
            canvas.saveState()
            canvas.setFillColor(self.background_color)
            canvas.rect(0, 0, A4[0], A4[1], fill=1)
            self._header_footer(canvas, doc)
            canvas.restoreState()

        self.doc.build(
            self.elements,
            onFirstPage=first_page,
            onLaterPages=later_pages,
        )

    def _generate_content(self):
        self._create_title("1. Overview", "Heading2")
        self._create_overview_metrics()
        self._create_title("Top 10 Keywords", "Heading3")
        self._create_keywords_chart(self.report.keywords)  # Pass the keywords here
        self._create_duplicate_pages_section()
        self._create_error_summary()
        self._create_page_analysis_overview()

        self._create_title("2. Page Analysis", "Heading2")
        for i, page in enumerate(self.report.pages, 1):
            self._create_page_details(i, page)

    def _create_overview_metrics(self):
        data = [
            ["Total Pages", "Analysis Time", "Errors", "Duplicate Pages"],
            [
                str(len(self.report.pages)),
                f"{self.report.total_time:.2f}s",
                str(len(self.report.errors) if self.report.errors else 0),
                str(
                    len(self.report.duplicate_pages)
                    if self.report.duplicate_pages
                    else 0
                ),
            ],
        ]
        self._create_table(data)

    def _create_keywords_chart(self, keywords):
        if keywords:
            plt.figure(figsize=(8, 4))
            print("-" * 100)
            print(keywords)
            print("-" * 100)
            try:
                keywords_list = [kw.word for kw in keywords[:10]]
                counts = [kw.count for kw in keywords[:10]]
            except:
                keywords_list = [kw[1] for kw in keywords[:10]]
                counts = [kw[0] for kw in keywords[:10]]
            plt.bar(
                keywords_list, counts, color=self.primary_color.rgb()
            )  # Use rgb() method instead of hexval
            plt.title("Top Keywords")
            plt.xlabel("Keyword")
            plt.ylabel("Count")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format="png")
            img_buffer.seek(0)

            img = Image(img_buffer)
            img.drawHeight = 3 * inch
            img.drawWidth = 6 * inch
            self.elements.append(img)
            plt.close()
        else:
            self._create_paragraph("No keywords found.")

    def _create_duplicate_pages_section(self):
        if self.report.duplicate_pages:
            self._create_title("Duplicate Pages", "Heading3")
            for i, duplicate_group in enumerate(self.report.duplicate_pages, 1):
                self._create_paragraph(
                    f"Group {i}: " + ", ".join(url for url in duplicate_group),
                    "BodyText",
                )

    def _create_error_summary(self):
        if self.report.errors:
            self._create_title("Error Summary", "Heading3")
            error_counts = {}
            for error in self.report.errors:
                error_counts[error] = error_counts.get(error, 0) + 1

            plt.figure(figsize=(6, 6))
            plt.pie(
                error_counts.values(), labels=error_counts.keys(), autopct="%1.1f%%"
            )
            plt.title("Error Distribution")
            plt.axis("equal")

            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format="png")
            img_buffer.seek(0)

            img = Image(img_buffer)
            img.drawHeight = 4 * inch
            img.drawWidth = 4 * inch
            self.elements.append(img)
            plt.close()

    def _create_page_analysis_overview(self):
        self._create_title("Page Analysis Overview", "Heading3")
        data = [["URL", "Title Length", "Description Length", "Word Count", "Warnings"]]
        for page in self.report.pages:
            data.append(
                [
                    page.url,
                    len(page.title),
                    len(page.description),
                    page.word_count,
                    len(page.warnings),
                ]
            )
        self._create_table(data)

    def _create_page_details(self, index, page):
        self._create_title(f"2.{index}. {page.url}", "Heading3")

        # Create a table for main page info
        data = [
            ["Word Count", "Title Length", "Description Length"],
            [page.word_count, len(page.title), len(page.description)],
        ]
        self._create_table(data)

        self._create_paragraph(f"Title: {page.title}")
        self._create_paragraph(f"Description: {page.description}")
        self._create_keywords_chart(page.keywords[:10])

        # Warnings
        if page.warnings:
            self._create_title("Warnings", "Heading4")
            grouped_warnings = self._group_warnings(page.warnings)
            for category, items in grouped_warnings.items():
                if isinstance(items, list):
                    self._create_paragraph(
                        f"{category}: " + ", ".join([item for item in items]),
                        "BodyText",
                    )
                else:
                    self._create_paragraph(f"{category}: {items}", "BodyText")

        # W3C Validation
        if page.w3c_validation:
            self._create_title("W3C Validation", "Heading4")
            w3c_results = page.w3c_validation
            data = [
                ["Total Messages", "Errors", "Warnings"],
                [
                    len(w3c_results.messages),
                    sum(1 for msg in w3c_results.messages if msg.type == "error"),
                    sum(1 for msg in w3c_results.messages if msg.type == "info"),
                ],
            ]
            self._create_table(data)

            for msg in w3c_results.messages:
                msg_type = (
                    "Error"
                    if msg.type == "error"
                    else "Warning" if msg.type == "info" else "Info"
                )
                self._create_paragraph(f"{msg_type}: {msg.message}", "BodyText")
                if (
                    msg.first_line
                    and msg.first_column
                    and msg.last_line
                    and msg.last_column
                ):
                    self._create_paragraph(
                        f"From line {msg.first_line}, column {msg.first_column}; to line {msg.last_line}, column {msg.last_column}",
                        "BodyText",
                    )
                if msg.extract:
                    self._create_paragraph(msg.extract, "Code")

        self.elements.append(PageBreak())

    def _group_warnings(self, warnings):
        grouped = {}
        pattern = r"^(.*?):\s*(.*)$"

        for warning in warnings:
            match = re.match(pattern, warning)
            if match:
                key, value = match.groups()
                if key in grouped:
                    if isinstance(grouped[key], list):
                        grouped[key].append(value)
                    else:
                        grouped[key] = [grouped[key], value]
                else:
                    grouped[key] = value
            else:
                # If the warning doesn't match the pattern, add it as is
                grouped[warning] = warning

        return grouped
