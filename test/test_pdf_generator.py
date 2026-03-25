import io
from ipaddress import ip_address

from reportlab.platypus import Flowable

import src.pdf_generator as pdf_generator_module
import src.url_safety as url_safety
from src.models import KeyWord, Page, Report, W3CMessage, W3CResponse


class FakeImage:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.drawHeight = kwargs.get("height", 0)
        self.drawWidth = kwargs.get("width", 0)


class FakePlotter:
    def figure(self, *args, **kwargs):
        return None

    def bar(self, *args, **kwargs):
        return None

    def title(self, *args, **kwargs):
        return None

    def xlabel(self, *args, **kwargs):
        return None

    def ylabel(self, *args, **kwargs):
        return None

    def xticks(self, *args, **kwargs):
        return None

    def tight_layout(self):
        return None

    def savefig(self, buffer, format):
        buffer.write(b"fake-image")

    def close(self):
        return None

    def pie(self, *args, **kwargs):
        return None

    def axis(self, *args, **kwargs):
        return None


class DummyLogo(Flowable):
    def __init__(self, width, height):
        super().__init__()
        self.drawWidth = width
        self.drawHeight = height

    def wrap(self, availWidth, availHeight):
        return self.drawWidth, self.drawHeight

    def draw(self):
        return None


def _install_pdf_story_test_doubles(monkeypatch):
    monkeypatch.setattr(pdf_generator_module, "Image", FakeImage)
    monkeypatch.setattr(pdf_generator_module, "plt", FakePlotter())
    monkeypatch.setattr(
        pdf_generator_module.PDFGenerator,
        "_get_logo",
        lambda self, url, width=0, height=0: FakeImage(
            url, width=width, height=height
        ),
    )


def _install_logo_fetch_test_doubles(monkeypatch):
    monkeypatch.setattr(pdf_generator_module, "Image", FakeImage)
    monkeypatch.setattr(pdf_generator_module, "plt", FakePlotter())


def _install_pdf_render_test_doubles(monkeypatch):
    monkeypatch.setattr(
        pdf_generator_module.PDFGenerator,
        "_get_logo",
        lambda self, url, width=0, height=0: DummyLogo(width or 100, height or 20),
    )
    monkeypatch.setattr(
        pdf_generator_module.PDFGenerator,
        "_create_keywords_chart",
        lambda self, keywords: self._create_paragraph("Chart placeholder"),
    )


def _make_page(url, *, with_validation=False):
    validation = None
    if with_validation:
        validation = W3CResponse(
            messages=[
                W3CMessage(
                    type="error",
                    subtype=None,
                    message="Invalid markup",
                    extract="<span>unsafe</span> code",
                    url=url,
                    first_line=3,
                    last_line=3,
                    first_column=5,
                    last_column=16,
                    hiliteStart=None,
                    hiliteLength=None,
                )
            ],
            url=url,
            source=None,
            language="en",
        )

    return Page(
        url=url,
        title="Example title for SEO testing",
        description="Useful description long enough to exercise the PDF generator.",
        word_count=420,
        keywords=[KeyWord(word="seo", count=5), KeyWord(word="audit", count=3)],
        bigrams=[],
        trigrams=[],
        warnings=["Title: Too short"],
        content_hash="hash",
        w3c_validation=validation,
    )


def _make_report(*pages):
    return Report(
        pages=list(pages),
        keywords=[KeyWord(word="seo", count=5), KeyWord(word="audit", count=3)],
        errors=[],
        total_time=1.23,
        duplicate_pages=[],
    )


def _paragraph_texts(story):
    return [
        element.getPlainText()
        for element in story
        if isinstance(element, pdf_generator_module.Paragraph)
    ]


def test_get_logo_fetches_only_allowlisted_https_urls(monkeypatch):
    generator = pdf_generator_module.PDFGenerator.__new__(pdf_generator_module.PDFGenerator)
    pdf_generator_module.PDFGenerator._logo_cache.clear()
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


def test_build_story_handles_http_urls_validation_extracts_and_keyword_models(
    monkeypatch, capsys
):
    _install_pdf_story_test_doubles(monkeypatch)
    report = _make_report(
        _make_page("http://example.com/blog/post", with_validation=True)
    )

    story = pdf_generator_module.PDFGenerator(report, "report.pdf").build_story()
    texts = _paragraph_texts(story)

    assert "example.com/blog/post" in texts
    assert "2. Keywords" in texts
    assert "Error: Invalid markup" in texts
    assert "unsafe code" in texts
    assert capsys.readouterr().out == ""


def test_generate_uses_real_page_numbers_in_table_of_contents(monkeypatch):
    _install_pdf_render_test_doubles(monkeypatch)
    report = _make_report(
        Page(
            url="https://example.com/one",
            title="Example title for SEO testing",
            description="Long content " * 2200,
            word_count=420,
            keywords=[KeyWord(word="seo", count=5), KeyWord(word="audit", count=3)],
            bigrams=[],
            trigrams=[],
            warnings=["Title: Too short"],
            content_hash="hash",
            w3c_validation=None,
        ),
        _make_page("https://example.com/two"),
    )

    output = io.BytesIO()
    generator = pdf_generator_module.PDFGenerator(report, output)
    generator.generate()
    pages_by_title = {
        entry[1]: entry[2] for entry in generator.table_of_contents._entries
    }

    assert output.getvalue().startswith(b"%PDF")
    assert pages_by_title["1. Overview"] == 3
    assert pages_by_title["3.2. https://example.com/two"] > pages_by_title[
        "3.1. https://example.com/one"
    ]


def test_pdf_generator_fetches_each_logo_url_only_once_per_instance(monkeypatch):
    _install_logo_fetch_test_doubles(monkeypatch)
    pdf_generator_module.PDFGenerator._logo_cache.clear()
    monkeypatch.setattr(
        url_safety,
        "_resolve_ip_addresses",
        lambda hostname: {ip_address("185.199.108.133")},
    )

    requests_made = []

    class FakeResponse:
        status_code = 200
        content = b"image-bytes"

        def raise_for_status(self):
            return None

    def fake_get(url, timeout, allow_redirects):
        requests_made.append((url, timeout, allow_redirects))
        return FakeResponse()

    monkeypatch.setattr(pdf_generator_module.requests, "get", fake_get)

    generator = pdf_generator_module.PDFGenerator(
        _make_report(_make_page("https://example.com")), "report.pdf"
    )
    generator.build_story()

    assert requests_made == [
        (generator.logo_url, 10, False),
        (generator.cover_logo_url, 10, False),
    ]


def test_pdf_generator_reuses_cached_logo_bytes_across_instances(monkeypatch):
    _install_logo_fetch_test_doubles(monkeypatch)
    pdf_generator_module.PDFGenerator._logo_cache.clear()
    monkeypatch.setattr(
        url_safety,
        "_resolve_ip_addresses",
        lambda hostname: {ip_address("185.199.108.133")},
    )

    requests_made = []

    class FakeResponse:
        status_code = 200
        content = b"image-bytes"

        def raise_for_status(self):
            return None

    def fake_get(url, timeout, allow_redirects):
        requests_made.append((url, timeout, allow_redirects))
        return FakeResponse()

    monkeypatch.setattr(pdf_generator_module.requests, "get", fake_get)

    report = _make_report(_make_page("https://example.com"))
    pdf_generator_module.PDFGenerator(report, "first.pdf")
    pdf_generator_module.PDFGenerator(report, "second.pdf")

    assert requests_made == [
        (
            "https://raw.githubusercontent.com/Nassim-Tecnologia/brand-assets/refs/heads/main/logo-marca-light-without-bg.png",
            10,
            False,
        ),
        (
            "https://raw.githubusercontent.com/Nassim-Tecnologia/brand-assets/refs/heads/main/logo-marca-dark-without-bg.png",
            10,
            False,
        ),
    ]
