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
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from datetime import datetime
from src.models import Report
from src.url_safety import validate_logo_url
from src.utils import group_warnings
import requests
from io import BytesIO
import re
from html import escape
import matplotlib.pyplot as plt
import io
from urllib.parse import urlsplit


class SEOReportDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        super().afterFlowable(flowable)

        toc_level = getattr(flowable, "_toc_level", None)
        if toc_level is None or not isinstance(flowable, Paragraph):
            return

        title = flowable.getPlainText()
        bookmark_name = getattr(flowable, "_bookmark_name", None)
        if bookmark_name is not None:
            self.canv.bookmarkPage(bookmark_name)
            self.canv.addOutlineEntry(title, bookmark_name, level=toc_level, closed=False)

        self.notify("TOCEntry", (toc_level, title, self.page, bookmark_name))


class PDFGenerator:
    _logo_cache: dict[str, bytes] = {}

    def __init__(self, report: Report, filename):
        self.report = report
        self.filename = filename
        self.doc = SEOReportDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        self.styles = getSampleStyleSheet()
        self.elements = []
        self.table_of_contents = None
        self._heading_index = 0
        self.logo_url = "https://raw.githubusercontent.com/Nassim-Tecnologia/brand-assets/refs/heads/main/logo-marca-light-without-bg.png"
        self.cover_logo_url = "https://raw.githubusercontent.com/Nassim-Tecnologia/brand-assets/refs/heads/main/logo-marca-dark-without-bg.png"
        self.logo_image = self._get_logo(self.logo_url)
        self.cover_logo_image = self._get_logo(
            self.cover_logo_url, width=3.75 * inch, height=1.25 * inch
        )

        # Define custom colors
        self.primary_color = colors.Color(red=0.827, green=0.247, blue=0.286)  # #D33F49
        self.background_color = colors.HexColor("#FBFFFE")
        self.text_color = colors.HexColor("#04080F")

        # Update styles
        self._update_styles()

    def _get_logo(self, url, width=1.5 * inch, height=0.5 * inch):
        image_bytes = self._get_logo_bytes(url)
        return Image(BytesIO(image_bytes), width=width, height=height)

    @classmethod
    def _get_logo_bytes(cls, url: str) -> bytes:
        safe_url = validate_logo_url(url)
        cached_bytes = cls._logo_cache.get(safe_url)
        if cached_bytes is not None:
            return cached_bytes

        response = requests.get(safe_url, timeout=10, allow_redirects=False)
        if 300 <= response.status_code < 400:
            raise ValueError("Logo URLs must not redirect.")
        response.raise_for_status()
        cls._logo_cache[safe_url] = response.content
        return response.content

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

        if "Code" not in self.styles.byName:
            self.styles.add(
                ParagraphStyle(
                    name="Code",
                    parent=self.styles["BodyText"],
                    fontName="Courier",
                    fontSize=9,
                    leading=11,
                    leftIndent=12,
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

    @classmethod
    def generate_bytes(cls, report: Report) -> bytes:
        buffer = BytesIO()
        cls(report, buffer).generate()
        return buffer.getvalue()

    def _create_title(self, text, style="Heading1", toc_level=None):
        paragraph = Paragraph(text, self.styles[style])
        if toc_level is not None:
            paragraph._toc_level = toc_level
            paragraph._bookmark_name = f"section-{self._heading_index}"
            self._heading_index += 1

        self.elements.append(paragraph)
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
        self.elements.append(Spacer(1, 30))  # Increased spacing
        self.elements.append(self.cover_logo_image)
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
            Paragraph(self._format_report_subject(self.report.pages[0].url), self.styles["Subtitle"])
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
        summary_style = ParagraphStyle(
            name="SummaryItem",
            parent=self.styles["Normal"],
            firstLineIndent=0,
            alignment=TA_LEFT,
            leading=14,
        )
        indented_summary_style = ParagraphStyle(
            name="IndentedSummaryItem",
            parent=summary_style,
            leftIndent=20,
        )

        self.table_of_contents = TableOfContents()
        self.table_of_contents.levelStyles = [summary_style, indented_summary_style]
        self.table_of_contents.dotsMinLevel = 0

        return [
            Paragraph("Table of Contents", self.styles["Heading1"]),
            Spacer(1, 20),
            self.table_of_contents,
        ]

    @staticmethod
    def _format_report_subject(url: str) -> str:
        parsed = urlsplit(url)
        if not parsed.netloc:
            return url

        path = "" if parsed.path in ("", "/") else parsed.path
        query = f"?{parsed.query}" if parsed.query else ""
        return f"{parsed.netloc}{path}{query}"

    def build_story(self):
        self.elements = []
        self._heading_index = 0

        # Create cover page (no header/footer)
        self._create_cover_page()

        self.elements.append(PageBreak())
        self.elements.extend(self._create_summary_page())
        self.elements.append(PageBreak())

        self._generate_content()

        return list(self.elements)

    def generate(self):
        story = self.build_story()

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

        self.doc.multiBuild(
            story,
            onFirstPage=first_page,
            onLaterPages=later_pages,
        )

    def _generate_content(self):
        self._create_title("1. Overview", "Heading2", toc_level=0)
        self._create_overview_metrics()
        self._create_title("2. Keywords", "Heading2", toc_level=0)
        self._create_title("Top 10 Keywords", "Heading3")
        self._create_keywords_chart(self.report.keywords)  # Pass the keywords here
        self._create_duplicate_pages_section()
        self._create_error_summary()
        self._create_page_analysis_overview()

        self._create_title("3. Page Analysis", "Heading2", toc_level=0)
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
            keywords_list = [kw.word for kw in keywords[:10]]
            counts = [kw.count for kw in keywords[:10]]
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
        self._create_title(f"3.{index}. {page.url}", "Heading3", toc_level=1)

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
            grouped_warnings = group_warnings(page.warnings)
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
