import src.ui as ui_module
from src.models import KeyWord, Page, Report


class FakeSpinner:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeStreamlit:
    def __init__(self):
        self.session_state = {}
        self.download_calls = []
        self.error_messages = []

    def spinner(self, _message):
        return FakeSpinner()

    def download_button(self, **kwargs):
        self.download_calls.append(kwargs)

    def error(self, message):
        self.error_messages.append(message)


def _make_report():
    return Report(
        pages=[
            Page(
                url="https://example.com",
                title="Example title",
                description="Example description for UI tests.",
                word_count=120,
                keywords=[KeyWord(word="seo", count=2)],
                bigrams=[],
                trigrams=[],
                warnings=[],
                content_hash="hash",
                w3c_validation=None,
            )
        ],
        keywords=[KeyWord(word="seo", count=2)],
        errors=[],
        total_time=0.4,
        duplicate_pages=[],
    )


def test_create_pdf_download_persists_bytes_for_later_reruns(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.session_state["report"] = _make_report()
    monkeypatch.setattr(ui_module, "st", fake_st)
    monkeypatch.setattr(
        ui_module.PDFGenerator,
        "generate_bytes",
        lambda report: b"%PDF-1.7 persisted-download",
    )

    ui_module.create_pdf_download()
    ui_module.render_pdf_download_button()

    assert fake_st.session_state["pdf_data"] == b"%PDF-1.7 persisted-download"
    assert fake_st.session_state["pdf_file_name"] == ui_module.PDF_FILE_NAME
    assert fake_st.download_calls == [
        {
            "label": "Download PDF Report",
            "data": b"%PDF-1.7 persisted-download",
            "file_name": ui_module.PDF_FILE_NAME,
            "mime": "application/pdf",
        }
    ]
    assert fake_st.error_messages == []


def test_reset_analysis_state_clears_stale_pdf_download_state(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.session_state.update(
        {
            "report": _make_report(),
            "suggestions": {"Title": ["Improve title"]},
            "selected_page": 0,
            "pdf_data": b"%PDF-old",
            "pdf_file_name": "old-report.pdf",
            "analysis_complete": True,
        }
    )
    monkeypatch.setattr(ui_module, "st", fake_st)

    ui_module.reset_analysis_state()

    assert "report" not in fake_st.session_state
    assert "suggestions" not in fake_st.session_state
    assert "selected_page" not in fake_st.session_state
    assert "pdf_data" not in fake_st.session_state
    assert "pdf_file_name" not in fake_st.session_state
    assert fake_st.session_state["analysis_complete"] is False
