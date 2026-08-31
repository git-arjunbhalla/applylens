from __future__ import annotations

from fastapi import HTTPException, UploadFile

from app.schemas.ai import RESUME_PDF_MAX_BYTES
from app.services.pdf_text import PDFTextError, extract_pdf_text

_PDF_CONTENT_TYPES = frozenset({"application/pdf", "application/x-pdf"})
_READ_CHUNK_SIZE = 64 * 1024


def _is_pdf_upload(upload: UploadFile) -> bool:
    content_type = (upload.content_type or "").split(";")[0].strip().lower()
    filename = (upload.filename or "").lower()
    return content_type in _PDF_CONTENT_TYPES or filename.endswith(".pdf")


async def extract_resume_text_from_upload(upload: UploadFile) -> str:
    """Validate a resume PDF upload and extract text in memory."""
    if not _is_pdf_upload(upload):
        raise HTTPException(
            status_code=422,
            detail="The resume must be a PDF file.",
        )

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(_READ_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > RESUME_PDF_MAX_BYTES:
            raise HTTPException(
                status_code=422,
                detail="The resume PDF must be 5 MB or smaller.",
            )
        chunks.append(chunk)

    data = b"".join(chunks)
    try:
        return extract_pdf_text(data)
    except PDFTextError as exc:
        raise HTTPException(
            status_code=422,
            detail=exc.message,
        ) from exc
