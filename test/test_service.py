import logging
from ipaddress import ip_address

import pytest

import src.service as service_module
import src.url_safety as url_safety
from src.models import KeyWord, Page, Report
from src.service import SEOAnalyzerService


def test_analyze_uses_normalized_safe_url(monkeypatch):
    monkeypatch.setattr(
        url_safety,
        "_resolve_ip_addresses",
        lambda hostname: {ip_address("93.184.216.34")},
    )

    captured = {}

    def fake_analyze(url):
        captured["url"] = url
        return {
            "pages": [],
            "keywords": [],
            "errors": [],
            "total_time": 0.0,
            "duplicate_pages": [],
        }

    monkeypatch.setattr(service_module, "analyze", fake_analyze)

    report = SEOAnalyzerService().analyze("HTTPS://Example.COM")

    assert captured["url"] == "https://example.com/"
    assert report.pages == []
    assert report.keywords == []
    assert report.total_time == 0.0


def test_analyze_normalizes_keywords_and_error_payloads(monkeypatch, caplog):
    monkeypatch.setattr(
        url_safety,
        "_resolve_ip_addresses",
        lambda hostname: {ip_address("93.184.216.34")},
    )

    def fake_analyze(url):
        return {
            "pages": [
                {
                    "url": url,
                    "title": "Example page title",
                    "description": "Example page description with enough content.",
                    "word_count": 320,
                    "keywords": [
                        (2, "seo"),
                        [1, "audit"],
                        {"word": "crawl", "count": "3"},
                        {"word": "broken"},
                    ],
                    "bigrams": [],
                    "trigrams": [],
                    "warnings": [],
                }
            ],
            "keywords": [{"word": "seo", "count": 2}],
            "errors": ["timeout", {"message": "invalid html", "code": 400}],
            "total_time": 0.2,
            "duplicate_pages": [],
        }

    monkeypatch.setattr(service_module, "analyze", fake_analyze)

    with caplog.at_level(logging.WARNING):
        report = SEOAnalyzerService().analyze("https://example.com")

    assert [(kw.word, kw.count) for kw in report.pages[0].keywords] == [
        ("seo", 2),
        ("audit", 1),
        ("crawl", 3),
    ]
    assert report.errors == ['timeout', '{"code": 400, "message": "invalid html"}']
    assert "Ignoring unsupported keyword payload" in caplog.text


def test_validate_page_rejects_internal_urls_before_fetch(monkeypatch):
    def fail_get(*args, **kwargs):
        raise AssertionError("requests.get should not be called for blocked URLs")

    def fail_post(*args, **kwargs):
        raise AssertionError("requests.post should not be called for blocked URLs")

    monkeypatch.setattr(service_module.requests, "get", fail_get)
    monkeypatch.setattr(service_module.requests, "post", fail_post)

    with pytest.raises(url_safety.UnsafeUrlError):
        SEOAnalyzerService().validate_page("http://127.0.0.1/admin")


def test_validate_page_fetches_html_and_parses_w3c_messages(monkeypatch):
    monkeypatch.setattr(
        url_safety,
        "_resolve_ip_addresses",
        lambda hostname: {ip_address("93.184.216.34")},
    )

    calls = {}

    class FakeResponse:
        def __init__(self, *, status_code=200, content=b"", payload=None):
            self.status_code = status_code
            self.content = content
            self._payload = payload or {}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError("HTTP error")

        def json(self):
            return self._payload

    def fake_get(url, timeout, allow_redirects):
        calls["get"] = {
            "url": url,
            "timeout": timeout,
            "allow_redirects": allow_redirects,
        }
        return FakeResponse(content=b"<html>page</html>")

    def fake_post(url, headers, data, timeout):
        calls["post"] = {
            "url": url,
            "headers": headers,
            "data": data,
            "timeout": timeout,
        }
        return FakeResponse(
            payload={
                "source": "uploaded",
                "language": "en",
                "messages": [
                    {
                        "type": "error",
                        "subType": "fatal",
                        "message": "Bad markup",
                        "extract": "<div>",
                        "url": "https://example.com/",
                        "firstLine": 7,
                        "lastLine": 7,
                        "firstColumn": 3,
                        "lastColumn": 8,
                        "hiliteStart": 1,
                        "hiliteLength": 5,
                    }
                ],
            }
        )

    monkeypatch.setattr(service_module.requests, "get", fake_get)
    monkeypatch.setattr(service_module.requests, "post", fake_post)

    result = SEOAnalyzerService().validate_page("https://example.com")

    assert calls["get"] == {
        "url": "https://example.com/",
        "timeout": 10,
        "allow_redirects": False,
    }
    assert calls["post"]["url"] == "https://validator.w3.org/nu/?out=json"
    assert calls["post"]["headers"] == {"Content-Type": "text/html; charset=utf-8"}
    assert calls["post"]["data"] == b"<html>page</html>"
    assert calls["post"]["timeout"] == 10
    assert result.url == "https://example.com/"
    assert result.source == "uploaded"
    assert result.language == "en"
    assert len(result.messages) == 1
    assert result.messages[0].message == "Bad markup"
    assert result.messages[0].first_line == 7
    assert result.messages[0].last_column == 8


def test_validate_page_stops_on_redirect_before_contacting_validator(monkeypatch):
    monkeypatch.setattr(
        url_safety,
        "_resolve_ip_addresses",
        lambda hostname: {ip_address("93.184.216.34")},
    )

    class RedirectResponse:
        status_code = 302
        content = b""

        def raise_for_status(self):
            return None

    def fake_post(*args, **kwargs):
        raise AssertionError("requests.post should not run after a redirect response")

    monkeypatch.setattr(service_module.requests, "get", lambda *args, **kwargs: RedirectResponse())
    monkeypatch.setattr(service_module.requests, "post", fake_post)

    with pytest.raises(
        ValueError, match="Redirects are not supported during W3C validation."
    ):
        SEOAnalyzerService().validate_page("https://example.com")


def test_generate_suggestions_covers_page_level_and_sitewide_rules():
    report = Report(
        pages=[
            Page(
                url="https://example.com",
                title="Short title",
                description="Short description",
                word_count=120,
                keywords=[KeyWord(word="seo", count=2)],
                warnings=[
                    "Missing title tag",
                    "Heading structure issue",
                    "Slow server response",
                ],
            )
        ],
        keywords=[KeyWord(word="seo", count=2)],
        errors=[],
        total_time=0.5,
        duplicate_pages=[],
    )

    suggestions = SEOAnalyzerService().generate_suggestions(report)

    assert any("too short" in item for item in suggestions["Title"])
    assert any("too short" in item for item in suggestions["Description"])
    assert any("adding more relevant keywords" in item for item in suggestions["Keywords"])
    assert any("lacks keyword diversity" in item for item in suggestions["Keywords"])
    assert any("thin" in item for item in suggestions["Content"])
    assert any("Missing title tag on https://example.com" == item for item in suggestions["Title"])
    assert any(
        "Heading structure issue on https://example.com" == item
        for item in suggestions["Structure"]
    )
    assert any(
        "Slow server response on https://example.com" == item
        for item in suggestions["Performance"]
    )
