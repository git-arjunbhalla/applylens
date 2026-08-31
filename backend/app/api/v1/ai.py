from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.ai_http import http_exception_from_ai_error
from app.api.deps import get_configured_ai_client, get_current_user
from app.models.user import User
from app.schemas.ai import (
    JDMatchRequest,
    JDMatchResult,
    ResumeAnalysisRequest,
    ResumeAnalysisResult,
)
from app.services.ai_client import AIClient
from app.services.ai_errors import AIError
from app.services.jd_match import match_job_description
from app.services.resume_analysis import analyze_resume

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/resume-analysis", response_model=ResumeAnalysisResult)
async def create_resume_analysis(
    payload: ResumeAnalysisRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
    client: Annotated[AIClient, Depends(get_configured_ai_client)],
) -> ResumeAnalysisResult:
    try:
        return await analyze_resume(
            payload.resume_text,
            payload.job_description,
            client,
        )
    except AIError as exc:
        raise http_exception_from_ai_error(exc) from exc


@router.post("/jd-match", response_model=JDMatchResult)
async def create_jd_match(
    payload: JDMatchRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
    client: Annotated[AIClient, Depends(get_configured_ai_client)],
) -> JDMatchResult:
    try:
        return await match_job_description(
            payload.resume_text,
            payload.job_description,
            client,
        )
    except AIError as exc:
        raise http_exception_from_ai_error(exc) from exc
