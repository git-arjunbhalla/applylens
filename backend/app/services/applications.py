from datetime import date

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.enums import ApplicationStatus
from app.schemas.application import (
    ApplicationCreate,
    ApplicationSortField,
    ApplicationUpdate,
    SortOrder,
)


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _owned_applications(user_id: int) -> Select[tuple[Application]]:
    return select(Application).where(Application.user_id == user_id)


async def get_owned_application(
    db: AsyncSession,
    user_id: int,
    application_id: int,
) -> Application | None:
    result = await db.execute(
        _owned_applications(user_id).where(Application.id == application_id)
    )
    return result.scalar_one_or_none()


def _apply_list_filters(
    stmt: Select[tuple[Application]],
    *,
    status: ApplicationStatus | None,
    company: str | None,
    deadline_before: date | None,
    deadline_after: date | None,
    search: str | None,
) -> Select[tuple[Application]]:
    if status is not None:
        stmt = stmt.where(Application.status == status)

    if company is not None:
        company_value = company.strip()
        if company_value:
            stmt = stmt.where(func.lower(Application.company_name) == company_value.lower())

    if deadline_before is not None:
        stmt = stmt.where(Application.deadline <= deadline_before)

    if deadline_after is not None:
        stmt = stmt.where(Application.deadline >= deadline_after)

    if search is not None:
        search_value = search.strip()
        if search_value:
            pattern = f"%{_escape_like(search_value.lower())}%"
            stmt = stmt.where(
                or_(
                    func.lower(Application.company_name).like(pattern, escape="\\"),
                    func.lower(Application.role_title).like(pattern, escape="\\"),
                )
            )

    return stmt


async def list_applications(
    db: AsyncSession,
    user_id: int,
    *,
    page: int,
    page_size: int,
    sort: ApplicationSortField,
    order: SortOrder,
    status: ApplicationStatus | None = None,
    company: str | None = None,
    deadline_before: date | None = None,
    deadline_after: date | None = None,
    search: str | None = None,
) -> tuple[list[Application], int]:
    filters = {
        "status": status,
        "company": company,
        "deadline_before": deadline_before,
        "deadline_after": deadline_after,
        "search": search,
    }
    base = _apply_list_filters(_owned_applications(user_id), **filters)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = int(await db.scalar(count_stmt) or 0)

    sort_column = getattr(Application, sort.value)
    if order is SortOrder.ASC:
        ordering = sort_column.asc().nulls_last()
        tiebreaker = Application.id.asc()
    else:
        ordering = sort_column.desc().nulls_last()
        tiebreaker = Application.id.desc()

    offset = (page - 1) * page_size
    result = await db.execute(
        base.order_by(ordering, tiebreaker).offset(offset).limit(page_size)
    )
    return list(result.scalars().all()), total


async def create_application(
    db: AsyncSession,
    user_id: int,
    payload: ApplicationCreate,
) -> Application:
    application = Application(user_id=user_id, **payload.model_dump())
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


async def update_application(
    db: AsyncSession,
    user_id: int,
    application_id: int,
    payload: ApplicationUpdate,
) -> Application | None:
    application = await get_owned_application(db, user_id, application_id)
    if application is None:
        return None

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(application, field, value)

    await db.commit()
    await db.refresh(application)
    return application


async def delete_application(
    db: AsyncSession,
    user_id: int,
    application_id: int,
) -> bool:
    application = await get_owned_application(db, user_id, application_id)
    if application is None:
        return False

    await db.delete(application)
    await db.commit()
    return True
