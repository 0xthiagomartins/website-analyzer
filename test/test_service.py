from ipaddress import ip_address
import logging

import pytest

import src.service as service_module
import src.url_safety as url_safety
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
