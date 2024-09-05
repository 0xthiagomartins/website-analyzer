import concurrent.futures
from pprint import pprint
from pyseoanalyzer import analyze
from src.models import Report, Page, KeyWord, W3CResponse, W3CMessage
from typing import Dict, Any, List
from collections import Counter
import requests
import time
import random
import logging


class SEOAnalyzerService:
    def __init__(self):
        self.url = None
        self.content = None
        self.metadata = {}

    def analyze(self, url: str) -> Report:
        self.url = url
        output = analyze(url)
        return self._create_report(output)

    def _create_report(self, output: Dict[str, Any]) -> Report:
        pages = [self._create_page(page_data) for page_data in output.get("pages", [])]
        keywords = [
            KeyWord(word=kw["word"], count=kw["count"])
            for kw in output.get("keywords", [])
        ]

        return Report(
            pages=pages,
            keywords=keywords,
            errors=output.get("errors", []),
            total_time=output.get("total_time", 0.0),
            duplicate_pages=output.get("duplicate_pages", []),
        )

    def _create_page(self, page_data: Dict[str, Any]) -> Page:
        return Page(
            url=page_data.get("url", ""),
            title=page_data.get("title", ""),
            description=page_data.get("description", ""),
            word_count=page_data.get("word_count", 0),
            keywords=page_data.get("keywords", []),
            bigrams=[Counter(bigram) for bigram in page_data.get("bigrams", [])],
            trigrams=[Counter(trigram) for trigram in page_data.get("trigrams", [])],
            warnings=page_data.get("warnings", []),
            content_hash=page_data.get("content_hash"),
            w3c_validation=None,
        )

    def validate_page(self, url: str) -> W3CResponse:
        """Validate a single page using the W3C Validator API"""
        h = {"Content-Type": "text/html; charset=utf-8"}
        u = "https://validator.w3.org/nu/?out=json"

        try:
            response = requests.get(url, timeout=10)
            d = response.content

            response = requests.post(u, headers=h, data=d, timeout=10)
            if response.status_code >= 400:
                print(f"W3C Validator API returned status code: {response.status_code}")
                return W3CResponse(messages=[], url=url, source=None, language=None)

            result = response.json()
            messages = []
            for msg in result.get("messages", []):
                last_line = msg.get("lastLine")
                first_line = msg.get("firstLine", last_line)
                first_column = msg.get("firstColumn")
                last_column = msg.get("lastColumn")
                hilite_start = msg.get("hiliteStart")
                hilite_length = msg.get("hiliteLength")
                messages.append(
                    W3CMessage(
                        type=msg.get("type"),
                        subtype=msg.get("subtype"),
                        message=msg.get("message"),
                        extract=msg.get("extract"),
                        first_line=first_line,
                        last_line=last_line,
                        first_column=first_column,
                        last_column=last_column,
                        hiliteStart=hilite_start,
                        hiliteLength=hilite_length,
                    )
                )
            return W3CResponse(
                messages=messages,
                url=url,
                source=result.get("source", None),
                language=result.get("language", None),
            )
        except Exception as e:
            print(f"Error validating {url}: {str(e)}")
            return W3CResponse(messages=[], url=url, source=None, language=None)

    def _generate_report(self):
        return {
            "url": self.url,
            "metadata": self.metadata,
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self):
        recommendations = []
        if len(self.metadata["title"]) < 30 or len(self.metadata["title"]) > 60:
            recommendations.append("Optimize title length (30-60 characters)")
        if (
            len(self.metadata["description"]) < 50
            or len(self.metadata["description"]) > 160
        ):
            recommendations.append(
                "Optimize meta description length (50-160 characters)"
            )
        if len(self.metadata["keywords"]) < 5:
            recommendations.append("Add more relevant keywords")
        if self.metadata["h1_count"] != 1:
            recommendations.append("Ensure there's exactly one H1 tag")
        if self.metadata["img_alt_count"] == 0:
            recommendations.append("Add alt text to images")
        return recommendations

    def generate_suggestions(self, report: Report) -> Dict[str, List[str]]:
        suggestions = {
            "Title": [],
            "Description": [],
            "Keywords": [],
            "Content": [],
            "Structure": [],
            "Performance": [],
        }

        for page in report.pages:
            # Title suggestions
            if len(page.title) < 30:
                suggestions["Title"].append(
                    f"The title for {page.url} is too short. Aim for 50-60 characters."
                )
            elif len(page.title) > 60:
                suggestions["Title"].append(
                    f"The title for {page.url} is too long. Keep it under 60 characters."
                )

            # Description suggestions
            if len(page.description) < 50:
                suggestions["Description"].append(
                    f"The meta description for {page.url} is too short. Aim for 150-160 characters."
                )
            elif len(page.description) > 160:
                suggestions["Description"].append(
                    f"The meta description for {page.url} is too long. Keep it under 160 characters."
                )

            # Keywords suggestions
            if len(page.keywords) < 5:
                suggestions["Keywords"].append(
                    f"Consider adding more relevant keywords to {page.url}"
                )

            # Content suggestions
            if page.word_count < 300:
                suggestions["Content"].append(
                    f"The content on {page.url} is thin. Consider adding more valuable content."
                )

            # Add more suggestions based on the warnings
            for warning in page.warnings:
                category = self._categorize_warning(warning)
                suggestions[category].append(f"{warning} on {page.url}")

        # Overall suggestions
        if len(report.keywords) < 10:
            suggestions["Keywords"].append(
                "Your website lacks keyword diversity. Consider expanding your content to cover more relevant topics."
            )

        return suggestions

    def _categorize_warning(self, warning: str) -> str:
        if "title" in warning.lower():
            return "Title"
        elif "description" in warning.lower():
            return "Description"
        elif "keyword" in warning.lower():
            return "Keywords"
        elif any(word in warning.lower() for word in ["content", "text", "word"]):
            return "Content"
        elif any(
            word in warning.lower() for word in ["structure", "heading", "h1", "h2"]
        ):
            return "Structure"
        else:
            return "Performance"
