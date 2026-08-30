from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.interview_round import InterviewRound
from app.schemas.interview import InterviewRoundCreate, InterviewRoundUpdate
from app.services.applications import get_owned_application


def _owned_interviews(user_id: int, application_id: int) -> Select[tuple[InterviewRound]]:
    return (
        select(InterviewRound)
        .join(Application, InterviewRound.application_id == Application.id)
        .where(
            InterviewRound.application_id == application_id,
            Application.user_id == user_id,
        )
    )


async def get_owned_interview(
    db: AsyncSession,
    user_id: int,
    application_id: int,
    interview_id: int,
) -> InterviewRound | None:
    result = await db.execute(
        _owned_interviews(user_id, application_id).where(InterviewRound.id == interview_id)
    )
    return result.scalar_one_or_none()


async def list_interviews(
    db: AsyncSession,
    user_id: int,
    application_id: int,
) -> list[InterviewRound] | None:
    application = await get_owned_application(db, user_id, application_id)
    if application is None:
        return None

    result = await db.execute(
        _owned_interviews(user_id, application_id).order_by(
            InterviewRound.scheduled_at.asc().nulls_last(),
            InterviewRound.id.asc(),
        )
    )
    return list(result.scalars().all())


async def create_interview(
    db: AsyncSession,
    user_id: int,
    application_id: int,
    payload: InterviewRoundCreate,
) -> InterviewRound | None:
    application = await get_owned_application(db, user_id, application_id)
    if application is None:
        return None

    interview = InterviewRound(
        application_id=application.id,
        **payload.model_dump(),
    )
    db.add(interview)
    await db.commit()
    await db.refresh(interview)
    return interview


async def update_interview(
    db: AsyncSession,
    user_id: int,
    application_id: int,
    interview_id: int,
    payload: InterviewRoundUpdate,
) -> tuple[InterviewRound | None, str | None]:
    application = await get_owned_application(db, user_id, application_id)
    if application is None:
        return None, "application"

    interview = await get_owned_interview(db, user_id, application_id, interview_id)
    if interview is None:
        return None, "interview"

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(interview, field, value)

    await db.commit()
    await db.refresh(interview)
    return interview, None


async def delete_interview(
    db: AsyncSession,
    user_id: int,
    application_id: int,
    interview_id: int,
) -> str | None:
    application = await get_owned_application(db, user_id, application_id)
    if application is None:
        return "application"

    interview = await get_owned_interview(db, user_id, application_id, interview_id)
    if interview is None:
        return "interview"

    await db.delete(interview)
    await db.commit()
    return None
