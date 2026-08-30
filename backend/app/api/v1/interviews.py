from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.interview import (
    InterviewRoundCreate,
    InterviewRoundPublic,
    InterviewRoundUpdate,
)
from app.services import interviews as interview_service

router = APIRouter(
    prefix="/applications/{application_id}/interviews",
    tags=["interviews"],
)

APPLICATION_NOT_FOUND = "Application not found"
INTERVIEW_NOT_FOUND = "Interview round not found"


@router.get("", response_model=list[InterviewRoundPublic])
async def list_interviews(
    application_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[InterviewRoundPublic]:
    interviews = await interview_service.list_interviews(
        db,
        current_user.id,
        application_id,
    )
    if interviews is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=APPLICATION_NOT_FOUND)
    return [InterviewRoundPublic.model_validate(item) for item in interviews]


@router.post("", response_model=InterviewRoundPublic, status_code=status.HTTP_201_CREATED)
async def create_interview(
    application_id: int,
    payload: InterviewRoundCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewRoundPublic:
    interview = await interview_service.create_interview(
        db,
        current_user.id,
        application_id,
        payload,
    )
    if interview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=APPLICATION_NOT_FOUND)
    return InterviewRoundPublic.model_validate(interview)


@router.put("/{interview_id}", response_model=InterviewRoundPublic)
async def update_interview(
    application_id: int,
    interview_id: int,
    payload: InterviewRoundUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewRoundPublic:
    interview, missing = await interview_service.update_interview(
        db,
        current_user.id,
        application_id,
        interview_id,
        payload,
    )
    if missing == "application":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=APPLICATION_NOT_FOUND)
    if missing == "interview" or interview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INTERVIEW_NOT_FOUND)
    return InterviewRoundPublic.model_validate(interview)


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview(
    application_id: int,
    interview_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    missing = await interview_service.delete_interview(
        db,
        current_user.id,
        application_id,
        interview_id,
    )
    if missing == "application":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=APPLICATION_NOT_FOUND)
    if missing == "interview":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INTERVIEW_NOT_FOUND)
