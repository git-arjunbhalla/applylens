from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.api.ai_http import http_exception_from_ai_error
from app.api.deps import get_configured_ai_client, get_current_user
from app.models.user import User
from app.schemas.ai import (
    CoverLetterRequest,
    CoverLetterResult,
    JDMatchRequest,
    JDMatchResult,
    ResumeAnalysisResult,
)
from app.services.ai_client import AIClient
from app.services.ai_errors import AIError
from app.services.cover_letter import generate_cover_letter
from app.services.jd_match import match_job_description
from app.services.resume_analysis import analyze_resume
from app.services.resume_pdf import extract_resume_text_from_upload

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/resume-analysis", response_model=ResumeAnalysisResult)
async def create_resume_analysis(
    resume: Annotated[UploadFile, File()],
    _current_user: Annotated[User, Depends(get_current_user)],
    client: Annotated[AIClient, Depends(get_configured_ai_client)],
) -> ResumeAnalysisResult:
    resume_text = await extract_resume_text_from_upload(resume)
    try:
        return await analyze_resume(resume_text, client)
    except AIError as exc:
        raise http_exception_from_ai_error(exc) from exc


@router.post("/jd-match", response_model=JDMatchResult)
async def create_jd_match(
    resume: Annotated[UploadFile, File()],
    job_description: Annotated[str, Form()],
    _current_user: Annotated[User, Depends(get_current_user)],
    client: Annotated[AIClient, Depends(get_configured_ai_client)],
) -> JDMatchResult:
    try:
        payload = JDMatchRequest(job_description=job_description)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc
    resume_text = await extract_resume_text_from_upload(resume)
    try:
        return await match_job_description(
            resume_text,
            payload.job_description,
            client,
        )
    except AIError as exc:
        raise http_exception_from_ai_error(exc) from exc


@router.post("/cover-letter", response_model=CoverLetterResult)
async def create_cover_letter(
    resume: Annotated[UploadFile, File()],
    job_description: Annotated[str, Form()],
    company: Annotated[str, Form()],
    role: Annotated[str, Form()],
    _current_user: Annotated[User, Depends(get_current_user)],
    client: Annotated[AIClient, Depends(get_configured_ai_client)],
) -> CoverLetterResult:
    try:
        payload = CoverLetterRequest(
            job_description=job_description,
            company=company,
            role=role,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc
    resume_text = await extract_resume_text_from_upload(resume)
    try:
        return await generate_cover_letter(
            resume_text,
            payload.job_description,
            payload.company,
            payload.role,
            client,
        )
    except AIError as exc:
        raise http_exception_from_ai_error(exc) from exc
