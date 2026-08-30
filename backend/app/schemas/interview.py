from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, model_validator

from app.models.enums import InterviewOutcome


def _require_aware_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("must include a timezone")
    return value


class InterviewRoundCreate(BaseModel):
    round_name: str = Field(min_length=1, max_length=255)
    scheduled_at: datetime | None = None
    notes: str | None = None
    outcome: InterviewOutcome = InterviewOutcome.PENDING

    @field_validator("round_name")
    @classmethod
    def strip_round_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("scheduled_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        return _require_aware_datetime(value)


class InterviewRoundUpdate(BaseModel):
    round_name: str | None = Field(default=None, min_length=1, max_length=255)
    scheduled_at: datetime | None = None
    notes: str | None = None
    outcome: InterviewOutcome | None = None

    @field_validator("round_name")
    @classmethod
    def strip_round_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("scheduled_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        return _require_aware_datetime(value)

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "InterviewRoundUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        return self


class InterviewRoundPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    round_name: str
    scheduled_at: datetime | None
    notes: str | None
    outcome: InterviewOutcome

    @field_serializer("scheduled_at")
    def serialize_scheduled_at(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            value = value.replace(tzinfo=timezone.utc)
        iso = value.isoformat()
        if iso.endswith("+00:00"):
            return iso.replace("+00:00", "Z")
        return iso
