import pymupdf


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        if doc.needs_pass:
            raise ValueError("PDF is password-protected")
        text = "".join(page.get_text() for page in doc)
    if not text.strip():
        raise ValueError("No extractable text in PDF")
    return text
