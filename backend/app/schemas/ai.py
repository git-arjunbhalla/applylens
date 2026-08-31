from pydantic import BaseModel, Field, field_validator

RESUME_ANALYSIS_TEXT_MAX_LENGTH = 50_000
RESUME_PDF_MAX_BYTES = 5 * 1024 * 1024
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


class ResumeAnalysisScoreBreakdown(BaseModel):
    ats_compatibility: int = Field(ge=MATCH_SCORE_MIN, le=MATCH_SCORE_MAX)
    content_strength: int = Field(ge=MATCH_SCORE_MIN, le=MATCH_SCORE_MAX)
    keyword_optimization: int = Field(ge=MATCH_SCORE_MIN, le=MATCH_SCORE_MAX)
    resume_structure: int = Field(ge=MATCH_SCORE_MIN, le=MATCH_SCORE_MAX)
    achievement_quality: int = Field(ge=MATCH_SCORE_MIN, le=MATCH_SCORE_MAX)


class ResumeRewriteSuggestion(BaseModel):
    original: str
    suggested: str
    reason: str

    @field_validator("original", "suggested", "reason")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return _strip_required_text(value)


class ResumeAnalysisResult(BaseModel):
    """Standalone ATS/resume-quality output. Incomplete provider JSON is rejected."""

    ats_score: int = Field(ge=MATCH_SCORE_MIN, le=MATCH_SCORE_MAX)
    score_breakdown: ResumeAnalysisScoreBreakdown
    strengths: list[str]
    issues: list[str]
    missing_sections: list[str]
    detected_skills: list[str]
    keyword_suggestions: list[str]
    improvement_suggestions: list[str]
    rewrite_suggestions: list[ResumeRewriteSuggestion]
    summary: str

    @field_validator(
        "strengths",
        "issues",
        "missing_sections",
        "detected_skills",
        "keyword_suggestions",
        "improvement_suggestions",
    )
    @classmethod
    def strip_list_items(cls, values: list[str]) -> list[str]:
        return _clean_string_list(values)

    @field_validator("summary")
    @classmethod
    def strip_summary(cls, value: str) -> str:
        return value.strip()


class JDMatchRequest(BaseModel):
    job_description: str = Field(min_length=1, max_length=RESUME_ANALYSIS_TEXT_MAX_LENGTH)

    @field_validator("job_description")
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


class CoverLetterRequest(BaseModel):
    job_description: str = Field(min_length=1, max_length=RESUME_ANALYSIS_TEXT_MAX_LENGTH)
    company: str = Field(min_length=1, max_length=255)
    role: str = Field(min_length=1, max_length=255)

    @field_validator("job_description", "company", "role")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return _strip_required_text(value)


class CoverLetterResult(BaseModel):
    """Cover letter draft. Incomplete or blank provider JSON is rejected."""

    cover_letter: str = Field(min_length=1)

    @field_validator("cover_letter")
    @classmethod
    def strip_cover_letter(cls, value: str) -> str:
        return _strip_required_text(value)
