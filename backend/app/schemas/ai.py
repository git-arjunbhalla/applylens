from pydantic import BaseModel, Field, field_validator

RESUME_ANALYSIS_TEXT_MAX_LENGTH = 50_000
MATCH_SCORE_MIN = 0
MATCH_SCORE_MAX = 100


def _strip_required_text(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("must not be blank")
    return stripped


def _clean_string_list(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    for item in values:
        text = item.strip()
        if text:
            cleaned.append(text)
    return cleaned


class ResumeAnalysisRequest(BaseModel):
    resume_text: str = Field(min_length=1, max_length=RESUME_ANALYSIS_TEXT_MAX_LENGTH)
    job_description: str = Field(min_length=1, max_length=RESUME_ANALYSIS_TEXT_MAX_LENGTH)

    @field_validator("resume_text", "job_description")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return _strip_required_text(value)


class ResumeAnalysisResult(BaseModel):
    """Structured AI output. Incomplete provider JSON is rejected, not filled in."""

    match_score: int = Field(ge=MATCH_SCORE_MIN, le=MATCH_SCORE_MAX)
    matching_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]

    @field_validator(
        "matching_skills",
        "missing_skills",
        "strengths",
        "weaknesses",
        "recommendations",
    )
    @classmethod
    def strip_list_items(cls, values: list[str]) -> list[str]:
        return _clean_string_list(values)


class JDMatchRequest(BaseModel):
    resume_text: str = Field(min_length=1, max_length=RESUME_ANALYSIS_TEXT_MAX_LENGTH)
    job_description: str = Field(min_length=1, max_length=RESUME_ANALYSIS_TEXT_MAX_LENGTH)

    @field_validator("resume_text", "job_description")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return _strip_required_text(value)


class JDMatchResult(BaseModel):
    """Keyword overlap output. Incomplete provider JSON is rejected, not filled in."""

    matched_keywords: list[str]
    missing_keywords: list[str]
    relevant_skills: list[str]
    important_requirements: list[str]
    match_score: int = Field(ge=MATCH_SCORE_MIN, le=MATCH_SCORE_MAX)

    @field_validator(
        "matched_keywords",
        "missing_keywords",
        "relevant_skills",
        "important_requirements",
    )
    @classmethod
    def strip_list_items(cls, values: list[str]) -> list[str]:
        return _clean_string_list(values)
