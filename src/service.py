import concurrent.futures
from pprint import pprint
from pyseoanalyzer import analyze
from src.models import Report, Page, KeyWord, W3CResponse, W3CMessage
from typing import Dict, Any, List
from collections import Counter
import requests
from threading import Lock
import time
import random


class SEOAnalyzerService:
    def __init__(self):
        self.url = None
        self.content = None
        self.metadata = {}
        self.lock = Lock()
        self.last_request_time = 0
        self.min_request_interval = 1  # Minimum 1 second between requests

    def analyze(self, url: str) -> Report:
        self.url = url
        output = analyze(url)
        return self._create_report(output)

    def _create_report(self, output: Dict[str, Any]) -> Report:
        pages = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_page = {
                executor.submit(self._create_page, page_data): page_data
                for page_data in output.get("pages", [])
            }
            for future in concurrent.futures.as_completed(future_to_page):
                try:
                    page = future.result()
                    with self.lock:
                        pages.append(page)
                except Exception as e:
                    print(f"Error creating page: {str(e)}")

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
        pprint(page_data.get("errors"))
        url = page_data.get("url", "")

        try:
            validation_results = self.__validate(url, "text/html")
        except Exception as e:
            print(f"W3C validation failed for {url}: {str(e)}")
            validation_results = []

        w3c_messages = [
            W3CMessage(
                type=msg.get("type", "info"),
                subtype=msg.get("subtype"),
                message=msg.get("message"),
                extract=msg.get("extract"),
                offset=msg.get("offset"),
                line=msg.get("line"),
                column=msg.get("column"),
                url=url,
            )
            for msg in validation_results
        ]

        w3c_response = W3CResponse(
            messages=w3c_messages,
            url=url,
            source=None,
            language=None,
        )

        return Page(
            url=url,
            title=page_data.get("title", ""),
            description=page_data.get("description", ""),
            word_count=page_data.get("word_count", 0),
            keywords=page_data.get("keywords", []),
            bigrams=[Counter(bigram) for bigram in page_data.get("bigrams", [])],
            trigrams=[Counter(trigram) for trigram in page_data.get("trigrams", [])],
            warnings=page_data.get("warnings", []),
            content_hash=page_data.get("content_hash"),
            w3c_validation=w3c_response,
        )

    def __validate(self, url: str, type: str) -> List[Dict[str, Any]]:
        """
        Start validation of files with rate limiting and retries
        """
        h = {"Content-Type": f"{type}; charset=utf-8"}
        u = "https://validator.w3.org/nu/?out=json"

        max_retries = 3
        base_delay = 2

        for attempt in range(max_retries):
            try:
                self._wait_for_rate_limit()

                response = requests.get(url, timeout=10)
                d = response.content

                self._wait_for_rate_limit()

                response = requests.post(u, headers=h, data=d, timeout=10)
                if response.status_code == 429:
                    delay = base_delay * (2**attempt) + random.uniform(0, 1)
                    print(f"Rate limit hit. Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                    continue

                if response.status_code >= 400:
                    print(
                        f"W3C Validator API returned status code: {response.status_code}"
                    )
                    return []

                result = response.json()
                return result.get("messages", [])
            except requests.Timeout:
                print(f"Timeout error while validating {url}")
            except requests.RequestException as e:
                print(f"Request error while validating {url}: {str(e)}")
            except Exception as e:
                print(f"Unexpected error during W3C validation of {url}: {str(e)}")

        print(f"Failed to validate {url} after {max_retries} attempts")
        return []

    def _wait_for_rate_limit(self):
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

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
