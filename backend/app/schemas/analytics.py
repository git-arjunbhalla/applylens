from pydantic import BaseModel, ConfigDict, Field


class StatusCounts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Wishlist: int = 0
    Applied: int = 0
    OA: int = 0
    Interviewing: int = 0
    Offer: int = 0
    Rejected: int = 0


class AnalyticsSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_applications: int
    counts_by_status: StatusCounts
    upcoming_deadlines: int
    interview_count: int
    offers: int
    rejections: int
    response_rate: float = Field(ge=0.0, le=1.0)
    average_time_to_response_days: float | None
