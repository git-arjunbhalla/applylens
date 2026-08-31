from __future__ import annotations

import pymupdf as fitz

from app.schemas.ai import RESUME_ANALYSIS_TEXT_MAX_LENGTH


class PDFTextError(Exception):
    """Raised when an uploaded PDF cannot be turned into usable resume text."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def extract_pdf_text(data: bytes) -> str:
    """Extract text from an in-memory PDF. Does not write files to disk."""
    if not data:
        raise PDFTextError("The uploaded PDF is empty.")
    if not data.startswith(b"%PDF"):
        raise PDFTextError("The resume must be a PDF file.")

    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise PDFTextError("The uploaded file is not a valid PDF.") from exc

    try:
        if document.needs_pass:
            raise PDFTextError("The uploaded PDF could not be read.")
        pages = [page.get_text() for page in document]
    finally:
        document.close()

    text = "\n".join(pages).strip()
    if not text:
        raise PDFTextError("No extractable text was found in the PDF.")
    if len(text) > RESUME_ANALYSIS_TEXT_MAX_LENGTH:
        raise PDFTextError("The extracted resume text is too long.")
    return text
