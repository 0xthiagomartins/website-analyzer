from ipaddress import ip_address

import src.pdf_generator as pdf_generator_module
import src.url_safety as url_safety


def test_get_logo_fetches_only_allowlisted_https_urls(monkeypatch):
    generator = pdf_generator_module.PDFGenerator.__new__(pdf_generator_module.PDFGenerator)
    monkeypatch.setattr(
        url_safety,
        "_resolve_ip_addresses",
        lambda hostname: {ip_address("185.199.108.133")},
    )

    calls = {}

    class FakeResponse:
        status_code = 200
        content = b"image-bytes"

        def raise_for_status(self):
            return None

    def fake_get(url, timeout, allow_redirects):
        calls["url"] = url
        calls["timeout"] = timeout
        calls["allow_redirects"] = allow_redirects
        return FakeResponse()

    monkeypatch.setattr(pdf_generator_module.requests, "get", fake_get)
    monkeypatch.setattr(
        pdf_generator_module,
        "Image",
        lambda data, width, height: {
            "content": data.getvalue(),
            "width": width,
            "height": height,
        },
    )

    image = generator._get_logo(
        "https://raw.githubusercontent.com/Nassim-Tecnologia/brand-assets/logo.png"
    )

    assert calls["url"] == (
        "https://raw.githubusercontent.com/Nassim-Tecnologia/brand-assets/logo.png"
    )
    assert calls["timeout"] == 10
    assert calls["allow_redirects"] is False
    assert image["content"] == b"image-bytes"
