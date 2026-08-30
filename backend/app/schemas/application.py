from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import ApplicationStatus


class ApplicationSortField(str, Enum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DEADLINE = "deadline"
    APPLIED_DATE = "applied_date"
    COMPANY_NAME = "company_name"
    ROLE_TITLE = "role_title"
    STATUS = "status"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class ApplicationCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    role_title: str = Field(min_length=1, max_length=255)
    status: ApplicationStatus = ApplicationStatus.WISHLIST
    applied_date: date | None = None
    deadline: date | None = None
    notes: str | None = None
    job_description: str | None = None
    resume_version: str | None = Field(default=None, max_length=255)

    @field_validator("company_name", "role_title", "resume_version")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class ApplicationUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    role_title: str | None = Field(default=None, min_length=1, max_length=255)
    status: ApplicationStatus | None = None
    applied_date: date | None = None
    deadline: date | None = None
    notes: str | None = None
    job_description: str | None = None
    resume_version: str | None = Field(default=None, max_length=255)

    @field_validator("company_name", "role_title", "resume_version")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "ApplicationUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        return self


class ApplicationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    company_name: str
    role_title: str
    status: ApplicationStatus
    applied_date: date | None
    deadline: date | None
    notes: str | None
    job_description: str | None
    resume_version: str | None
    created_at: datetime
    updated_at: datetime


class ApplicationListResponse(BaseModel):
    items: list[ApplicationPublic]
    total: int
    page: int
    page_size: int
