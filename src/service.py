import json
import logging
from pyseoanalyzer import analyze
from src.models import Report, Page, KeyWord, W3CResponse, W3CMessage
from src.url_safety import validate_public_url
from collections import Counter
import requests


logger = logging.getLogger(__name__)


class SEOAnalyzerService:
    def analyze(self, url: str) -> Report:
        safe_url = validate_public_url(url)
        output = analyze(safe_url)
        return self._create_report(output)

    def _create_report(self, output: dict[str, object]) -> Report:
        pages = [self._create_page(page_data) for page_data in output.get("pages", [])]
        keywords = self._normalize_keywords(output.get("keywords", []))

        return Report(
            pages=pages,
            keywords=keywords,
            errors=self._normalize_errors(output.get("errors", [])),
            total_time=output.get("total_time", 0.0),
            duplicate_pages=output.get("duplicate_pages", []),
        )

    def _create_page(self, page_data: dict[str, object]) -> Page:
        return Page(
            url=page_data.get("url", ""),
            title=page_data.get("title", ""),
            description=page_data.get("description", ""),
            word_count=page_data.get("word_count", 0),
            keywords=self._normalize_keywords(page_data.get("keywords", [])),
            bigrams=[Counter(bigram) for bigram in page_data.get("bigrams", [])],
            trigrams=[Counter(trigram) for trigram in page_data.get("trigrams", [])],
            warnings=page_data.get("warnings", []),
            content_hash=page_data.get("content_hash"),
            w3c_validation=None,
        )

    def _normalize_keywords(self, raw_keywords: object) -> list[KeyWord]:
        if not isinstance(raw_keywords, list):
            return []

        normalized_keywords = []
        for raw_keyword in raw_keywords:
            keyword = self._normalize_keyword(raw_keyword)
            if keyword is None:
                logger.warning("Ignoring unsupported keyword payload: %r", raw_keyword)
                continue
            normalized_keywords.append(keyword)

        return normalized_keywords

    def _normalize_keyword(self, raw_keyword: object) -> KeyWord | None:
        if isinstance(raw_keyword, KeyWord):
            return raw_keyword

        if isinstance(raw_keyword, dict):
            word = raw_keyword.get("word")
            count = raw_keyword.get("count")
        elif isinstance(raw_keyword, (list, tuple)) and len(raw_keyword) >= 2:
            count, word = raw_keyword[0], raw_keyword[1]
        else:
            return None

        if word is None or count is None:
            return None

        try:
            return KeyWord(word=str(word), count=int(count))
        except (TypeError, ValueError):
            return None

    def _normalize_errors(self, raw_errors: object) -> list[str]:
        if not isinstance(raw_errors, list):
            return []

        return [self._stringify_error(error) for error in raw_errors]

    def _stringify_error(self, error: object) -> str:
        if isinstance(error, str):
            return error

        try:
            return json.dumps(error, sort_keys=True)
        except (TypeError, ValueError):
            return str(error)

    def validate_page(self, url: str) -> W3CResponse:
        """Validate a single page using the W3C Validator API"""
        headers = {"Content-Type": "text/html; charset=utf-8"}
        validator_url = "https://validator.w3.org/nu/?out=json"
        safe_url = validate_public_url(url)

        page_response = requests.get(safe_url, timeout=10, allow_redirects=False)
        if 300 <= page_response.status_code < 400:
            raise ValueError("Redirects are not supported during W3C validation.")
        page_response.raise_for_status()

        validator_response = requests.post(
            validator_url,
            headers=headers,
            data=page_response.content,
            timeout=10,
        )
        validator_response.raise_for_status()

        result = validator_response.json()
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
                    subtype=msg.get("subType"),
                    message=msg.get("message"),
                    extract=msg.get("extract"),
                    url=msg.get("url"),
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
            url=safe_url,
            source=result.get("source", None),
            language=result.get("language", None),
        )

    def generate_suggestions(self, report: Report) -> dict[str, list[str]]:
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
