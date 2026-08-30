from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.enums import ApplicationStatus
from app.models.interview_round import InterviewRound
from app.schemas.analytics import AnalyticsSummary, StatusCounts

# Submitted applications that have left Wishlist. "Applied" is submitted
# but not yet a response. OA and later statuses count as a response.
_RESPONDED_STATUSES = (
    ApplicationStatus.OA,
    ApplicationStatus.INTERVIEWING,
    ApplicationStatus.OFFER,
    ApplicationStatus.REJECTED,
)


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def upcoming_deadline_window(today: date) -> tuple[date, date]:
    """Inclusive window: today through today + 7 calendar days (UTC date)."""
    return today, today + timedelta(days=7)


async def get_summary(
    db: AsyncSession,
    user_id: int,
    *,
    today: date | None = None,
) -> AnalyticsSummary:
    today = today or utc_today()
    window_start, window_end = upcoming_deadline_window(today)

    status_rows = (
        await db.execute(
            select(Application.status, func.count())
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
    ).all()

    counts = {status: 0 for status in ApplicationStatus}
    for status, count in status_rows:
        counts[status] = int(count)

    total = sum(counts.values())
    submitted = total - counts[ApplicationStatus.WISHLIST]
    responded = sum(counts[status] for status in _RESPONDED_STATUSES)
    response_rate = (responded / submitted) if submitted else 0.0

    upcoming = int(
        await db.scalar(
            select(func.count())
            .select_from(Application)
            .where(
                Application.user_id == user_id,
                Application.deadline >= window_start,
                Application.deadline <= window_end,
            )
        )
        or 0
    )

    interview_count = int(
        await db.scalar(
            select(func.count())
            .select_from(InterviewRound)
            .join(Application, InterviewRound.application_id == Application.id)
            .where(Application.user_id == user_id)
        )
        or 0
    )

    return AnalyticsSummary(
        total_applications=total,
        counts_by_status=StatusCounts(
            Wishlist=counts[ApplicationStatus.WISHLIST],
            Applied=counts[ApplicationStatus.APPLIED],
            OA=counts[ApplicationStatus.OA],
            Interviewing=counts[ApplicationStatus.INTERVIEWING],
            Offer=counts[ApplicationStatus.OFFER],
            Rejected=counts[ApplicationStatus.REJECTED],
        ),
        upcoming_deadlines=upcoming,
        interview_count=interview_count,
        offers=counts[ApplicationStatus.OFFER],
        rejections=counts[ApplicationStatus.REJECTED],
        response_rate=response_rate,
        average_time_to_response_days=None,
    )
