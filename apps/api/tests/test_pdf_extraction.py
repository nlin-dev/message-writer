import pymupdf
import pytest

from app.services.pdf_extraction import extract_text_from_pdf


def _make_pdf(text: str | None = None) -> bytes:
    with pymupdf.open() as doc:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text)
        return doc.tobytes()


class TestExtractTextFromPdf:
    def test_extracts_text_from_valid_pdf(self):
        pdf_bytes = _make_pdf("Hello extraction test")
        result = extract_text_from_pdf(pdf_bytes)
        assert "Hello extraction test" in result

    def test_raises_on_empty_pdf(self):
        pdf_bytes = _make_pdf()
        with pytest.raises(ValueError, match="No extractable text"):
            extract_text_from_pdf(pdf_bytes)


class TestUploadEndpoint:
    def test_upload_valid_pdf(self, client):
        pdf_bytes = _make_pdf("Sample research content for chunking.")
        resp = client.post(
            "/references/upload",
            files={"file": ("paper.pdf", pdf_bytes, "application/pdf")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "processed"
        assert data["char_count"] > 0
        assert data["chunk_count"] > 0
        assert "reference_id" in data

