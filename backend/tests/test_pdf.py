import pymupdf as fitz

from app.services.pdf_text import PDFTextError, extract_pdf_text


def _pdf_with_text(text: str | None) -> bytes:
    document = fitz.open()
    page = document.new_page()
    if text:
        page.insert_text((72, 72), text)
    data = document.tobytes()
    document.close()
    return data


def test_extracts_text_from_valid_pdf() -> None:
    text = extract_pdf_text(_pdf_with_text("Python developer with FastAPI."))
    assert "Python developer with FastAPI." in text


def test_rejects_empty_bytes() -> None:
    try:
        extract_pdf_text(b"")
        raise AssertionError("expected PDFTextError")
    except PDFTextError as exc:
        assert exc.message == "The uploaded PDF is empty."


def test_rejects_non_pdf_bytes() -> None:
    try:
        extract_pdf_text(b"this is a resume in plain text")
        raise AssertionError("expected PDFTextError")
    except PDFTextError as exc:
        assert exc.message == "The resume must be a PDF file."


def test_rejects_malformed_pdf_header() -> None:
    try:
        extract_pdf_text(b"%PDF-not-a-real-document")
        raise AssertionError("expected PDFTextError")
    except PDFTextError as exc:
        assert exc.message == "The uploaded file is not a valid PDF."


def test_rejects_pdf_with_no_extractable_text() -> None:
    try:
        extract_pdf_text(_pdf_with_text(None))
        raise AssertionError("expected PDFTextError")
    except PDFTextError as exc:
        assert exc.message == "No extractable text was found in the PDF."


def test_rejects_whitespace_only_extracted_text() -> None:
    try:
        extract_pdf_text(_pdf_with_text("   \n\t  "))
        raise AssertionError("expected PDFTextError")
    except PDFTextError as exc:
        assert exc.message == "No extractable text was found in the PDF."
