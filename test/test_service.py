from ipaddress import ip_address

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


def test_validate_page_rejects_internal_urls_before_fetch(monkeypatch):
    def fail_get(*args, **kwargs):
        raise AssertionError("requests.get should not be called for blocked URLs")

    def fail_post(*args, **kwargs):
        raise AssertionError("requests.post should not be called for blocked URLs")

    monkeypatch.setattr(service_module.requests, "get", fail_get)
    monkeypatch.setattr(service_module.requests, "post", fail_post)

    with pytest.raises(url_safety.UnsafeUrlError):
        SEOAnalyzerService().validate_page("http://127.0.0.1/admin")
