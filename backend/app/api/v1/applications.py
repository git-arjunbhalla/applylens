from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import ApplicationStatus
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationListResponse,
    ApplicationPublic,
    ApplicationSortField,
    ApplicationUpdate,
    SortOrder,
)
from app.services import applications as application_service

router = APIRouter(prefix="/applications", tags=["applications"])

NOT_FOUND_DETAIL = "Application not found"


@router.get("", response_model=ApplicationListResponse)
async def list_applications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    sort: Annotated[ApplicationSortField, Query()] = ApplicationSortField.CREATED_AT,
    order: Annotated[SortOrder, Query()] = SortOrder.DESC,
    status_filter: Annotated[ApplicationStatus | None, Query(alias="status")] = None,
    company: str | None = None,
    deadline_before: date | None = None,
    deadline_after: date | None = None,
    search: str | None = None,
) -> ApplicationListResponse:
    items, total = await application_service.list_applications(
        db,
        current_user.id,
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
        status=status_filter,
        company=company,
        deadline_before=deadline_before,
        deadline_after=deadline_after,
        search=search,
    )
    return ApplicationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ApplicationPublic, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApplicationPublic:
    application = await application_service.create_application(
        db,
        current_user.id,
        payload,
    )
    return ApplicationPublic.model_validate(application)


@router.get("/{application_id}", response_model=ApplicationPublic)
async def get_application(
    application_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApplicationPublic:
    application = await application_service.get_owned_application(
        db,
        current_user.id,
        application_id,
    )
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_DETAIL)
    return ApplicationPublic.model_validate(application)


@router.put("/{application_id}", response_model=ApplicationPublic)
async def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApplicationPublic:
    application = await application_service.update_application(
        db,
        current_user.id,
        application_id,
        payload,
    )
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_DETAIL)
    return ApplicationPublic.model_validate(application)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    deleted = await application_service.delete_application(
        db,
        current_user.id,
        application_id,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_DETAIL)
