import inspect
from pathlib import Path
from typing import Any

import pymupdf as fitz
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.api.deps import get_configured_ai_client
from app.core.config import Settings
from app.main import app
from app.schemas.ai import CoverLetterResult, ResumeAnalysisResult
from app.services.rate_limit import (
    AI_RATE_LIMIT_DETAIL,
    RATE_LIMIT_KEY_PREFIX,
    AIRateLimiter,
    RedisRateLimitBackend,
    get_ai_rate_limiter,
    rate_limit_key,
    window_id_and_ttl,
)

from tests.conftest import FakeRateLimitBackend

SIGNUP_PATH = "/api/v1/auth/signup"
ANALYSIS_PATH = "/api/v1/ai/resume-analysis"
MATCH_PATH = "/api/v1/ai/jd-match"
COVER_LETTER_PATH = "/api/v1/ai/cover-letter"

VALID_RESUME = "Python developer with FastAPI and PostgreSQL experience."
VALID_JD = "Looking for a Python engineer with FastAPI and PostgreSQL."
VALID_COMPANY = "Acme Labs"
VALID_ROLE = "Backend Engineer"

VALID_ANALYSIS = {
    "ats_score": 78,
    "score_breakdown": {
        "ats_compatibility": 80,
        "content_strength": 74,
        "keyword_optimization": 70,
        "resume_structure": 82,
        "achievement_quality": 68,
    },
    "strengths": ["Clear backend stack listed"],
    "issues": ["Few measurable outcomes"],
    "missing_sections": ["Professional summary"],
    "detected_skills": ["Python", "FastAPI", "PostgreSQL"],
    "keyword_suggestions": ["REST APIs"],
    "improvement_suggestions": ["Add quantified results"],
    "rewrite_suggestions": [
        {
            "original": "Worked on backend services",
            "suggested": "Built FastAPI services",
            "reason": "Names tools already present",
        }
    ],
    "summary": "Solid technical resume.",
}

VALID_MATCH = {
    "matched_keywords": ["Python", "FastAPI", "PostgreSQL"],
    "missing_keywords": ["Docker"],
    "relevant_skills": ["Python", "FastAPI"],
    "important_requirements": ["Backend development experience"],
    "match_score": 78,
}

VALID_LETTER = {"cover_letter": "Dear Hiring Manager,\n\nDraft grounded in the resume.\n"}


class FakeAIClient:
    def __init__(
        self,
        *,
        result: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.calls: list[tuple[str, type[BaseModel] | None]] = []

    def generate_json(
        self,
        prompt: str,
        schema: type[BaseModel] | None = None,
    ) -> dict[str, Any]:
        self.calls.append((prompt, schema))
        if self.error is not None:
            raise self.error
        assert self.result is not None
        if schema is not None:
            return schema.model_validate(self.result).model_dump()
        return self.result


def _make_pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    data = document.tobytes()
    document.close()
    return data


def _resume_file(data: bytes) -> dict:
    return {"resume": ("resume.pdf", data, "application/pdf")}


def _signup(client: TestClient, email: str = "user@example.com") -> dict:
    response = client.post(
        SIGNUP_PATH,
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201
    return response.json()


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _override_ai(fake: FakeAIClient) -> None:
    app.dependency_overrides[get_configured_ai_client] = lambda: fake


def _override_limiter(limiter: AIRateLimiter) -> None:
    app.dependency_overrides[get_ai_rate_limiter] = lambda: limiter


def _pdf() -> dict:
    return _resume_file(_make_pdf_bytes(VALID_RESUME))


def test_rate_limit_key_uses_namespace_user_and_window() -> None:
    assert rate_limit_key(42, 123456) == f"{RATE_LIMIT_KEY_PREFIX}:42:123456"


def test_window_id_and_ttl_are_fixed_window() -> None:
    window_id, ttl = window_id_and_ttl(3600.0, 3600)
    assert window_id == 1
    assert ttl == 3600
    window_id, ttl = window_id_and_ttl(3599.2, 3600)
    assert window_id == 0
    assert ttl == 1


async def _hit(limiter: AIRateLimiter, user_id: int) -> Any:
    return await limiter.hit(user_id, now=1_700_000_000.0)


def test_first_request_is_allowed() -> None:
    import asyncio

    backend = FakeRateLimitBackend()
    limiter = AIRateLimiter(backend, max_requests=10, window_seconds=3600)
    decision = asyncio.run(_hit(limiter, 1))
    assert decision.allowed is True
    assert decision.count == 1
    assert decision.key.startswith(f"{RATE_LIMIT_KEY_PREFIX}:1:")


def test_requests_below_limit_are_allowed() -> None:
    import asyncio

    backend = FakeRateLimitBackend()
    limiter = AIRateLimiter(backend, max_requests=10, window_seconds=3600)
    for expected in range(1, 10):
        decision = asyncio.run(_hit(limiter, 7))
        assert decision.allowed is True
        assert decision.count == expected


def test_request_exactly_at_limit_is_allowed() -> None:
    import asyncio

    backend = FakeRateLimitBackend()
    limiter = AIRateLimiter(backend, max_requests=10, window_seconds=3600)
    for expected in range(1, 11):
        decision = asyncio.run(_hit(limiter, 5))
        assert decision.allowed is True
        assert decision.count == expected


def test_request_exceeding_limit_is_denied() -> None:
    import asyncio

    backend = FakeRateLimitBackend()
    limiter = AIRateLimiter(backend, max_requests=10, window_seconds=3600)
    for _ in range(10):
        assert asyncio.run(_hit(limiter, 3)).allowed is True
    denied = asyncio.run(_hit(limiter, 3))
    assert denied.allowed is False
    assert denied.retry_after_seconds >= 1


def test_new_window_resets_counter() -> None:
    import asyncio

    backend = FakeRateLimitBackend()
    limiter = AIRateLimiter(backend, max_requests=2, window_seconds=3600)
    now = 1_700_000_000.0
    assert asyncio.run(limiter.hit(1, now=now)).allowed is True
    assert asyncio.run(limiter.hit(1, now=now)).allowed is True
    assert asyncio.run(limiter.hit(1, now=now)).allowed is False
    next_window = asyncio.run(limiter.hit(1, now=now + 3600))
    assert next_window.allowed is True
    assert next_window.count == 1


def test_fail_open_log_does_not_include_redis_url() -> None:
    import asyncio
    from unittest.mock import patch

    backend = FakeRateLimitBackend(fail=True)
    limiter = AIRateLimiter(backend, max_requests=1, window_seconds=3600)
    with patch("app.services.rate_limit.logger.warning") as warning:
        decision = asyncio.run(_hit(limiter, 1))
    assert decision.allowed is True
    warning.assert_called_once()
    logged = " ".join(str(arg) for arg in warning.call_args[0])
    assert "fail-open" in logged
    assert "redis://" not in logged.lower()
    assert "localhost:6379" not in logged


def test_different_users_have_independent_limits() -> None:
    import asyncio

    backend = FakeRateLimitBackend()
    limiter = AIRateLimiter(backend, max_requests=2, window_seconds=3600)
    assert asyncio.run(_hit(limiter, 1)).allowed is True
    assert asyncio.run(_hit(limiter, 1)).allowed is True
    assert asyncio.run(_hit(limiter, 1)).allowed is False
    assert asyncio.run(_hit(limiter, 2)).allowed is True


def test_redis_failure_fails_open() -> None:
    import asyncio

    backend = FakeRateLimitBackend(fail=True)
    limiter = AIRateLimiter(backend, max_requests=1, window_seconds=3600)
    first = asyncio.run(_hit(limiter, 1))
    second = asyncio.run(_hit(limiter, 1))
    assert first.allowed is True
    assert second.allowed is True


def test_empty_redis_url_is_handled_without_hardcoded_credentials() -> None:
    import asyncio

    backend = RedisRateLimitBackend("")
    limiter = AIRateLimiter(backend, max_requests=1, window_seconds=3600)
    decision = asyncio.run(_hit(limiter, 1))
    assert decision.allowed is True


def test_invalid_redis_url_fails_open() -> None:
    import asyncio

    backend = RedisRateLimitBackend("not-a-valid-redis-url")
    limiter = AIRateLimiter(backend, max_requests=1, window_seconds=3600)
    decision = asyncio.run(_hit(limiter, 1))
    assert decision.allowed is True


def test_redis_url_loaded_from_environment(monkeypatch: Any) -> None:
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/2")
    monkeypatch.setenv("AI_RATE_LIMIT_REQUESTS", "10")
    monkeypatch.setenv("AI_RATE_LIMIT_WINDOW_SECONDS", "3600")
    cfg = Settings(_env_file=None)
    assert cfg.redis_url == "redis://localhost:6379/2"
    assert cfg.ai_rate_limit_requests == 10
    assert cfg.ai_rate_limit_window_seconds == 3600


def test_no_redis_credentials_hardcoded() -> None:
    config_source = Path("app/core/config.py").read_text(encoding="utf-8")
    limiter_source = inspect.getsource(RedisRateLimitBackend)
    assert "redis://:" not in config_source
    assert "password" not in limiter_source.lower()
    default = Settings.model_fields["redis_url"].default
    assert default == "redis://localhost:6379/0"
    assert "@" not in default


def test_ai_rate_limit_http_first_request_allowed(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)
    response = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        files=_pdf(),
    )
    assert response.status_code == 200
    assert fake.calls


def test_ai_rate_limit_http_429_and_retry_after(client: TestClient) -> None:
    backend = FakeRateLimitBackend()
    limiter = AIRateLimiter(backend, max_requests=2, window_seconds=3600)
    _override_limiter(limiter)
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)
    headers = _auth_headers(tokens["access_token"])

    first = client.post(ANALYSIS_PATH, headers=headers, files=_pdf())
    second = client.post(ANALYSIS_PATH, headers=headers, files=_pdf())
    third = client.post(ANALYSIS_PATH, headers=headers, files=_pdf())

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.json()["detail"] == AI_RATE_LIMIT_DETAIL
    assert "Retry-After" in third.headers
    assert int(third.headers["Retry-After"]) >= 1
    assert "redis" not in third.text.lower()
    assert len(fake.calls) == 2


def test_ai_endpoints_share_per_user_quota(client: TestClient) -> None:
    backend = FakeRateLimitBackend()
    limiter = AIRateLimiter(backend, max_requests=10, window_seconds=3600)
    _override_limiter(limiter)
    tokens = _signup(client)
    headers = _auth_headers(tokens["access_token"])

    analysis_ai = FakeAIClient(result=VALID_ANALYSIS)
    match_ai = FakeAIClient(result=VALID_MATCH)
    letter_ai = FakeAIClient(result=VALID_LETTER)

    _override_ai(analysis_ai)
    for _ in range(5):
        response = client.post(ANALYSIS_PATH, headers=headers, files=_pdf())
        assert response.status_code == 200

    _override_ai(match_ai)
    for _ in range(4):
        response = client.post(
            MATCH_PATH,
            headers=headers,
            files=_pdf(),
            data={"job_description": VALID_JD},
        )
        assert response.status_code == 200

    _override_ai(letter_ai)
    tenth = client.post(
        COVER_LETTER_PATH,
        headers=headers,
        files=_pdf(),
        data={
            "job_description": VALID_JD,
            "company": VALID_COMPANY,
            "role": VALID_ROLE,
        },
    )
    assert tenth.status_code == 200
    assert CoverLetterResult.model_validate(tenth.json())

    eleventh = client.post(ANALYSIS_PATH, headers=headers, files=_pdf())
    assert eleventh.status_code == 429
    assert eleventh.json()["detail"] == AI_RATE_LIMIT_DETAIL


def test_different_users_independent_http_quota(client: TestClient) -> None:
    backend = FakeRateLimitBackend()
    limiter = AIRateLimiter(backend, max_requests=1, window_seconds=3600)
    _override_limiter(limiter)
    user_a = _signup(client, "a@example.com")
    user_b = _signup(client, "b@example.com")
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)

    first_a = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(user_a["access_token"]),
        files=_pdf(),
    )
    second_a = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(user_a["access_token"]),
        files=_pdf(),
    )
    first_b = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(user_b["access_token"]),
        files=_pdf(),
    )

    assert first_a.status_code == 200
    assert second_a.status_code == 429
    assert first_b.status_code == 200


def test_client_cannot_choose_another_users_rate_limit_key(client: TestClient) -> None:
    backend = FakeRateLimitBackend()
    limiter = AIRateLimiter(backend, max_requests=1, window_seconds=3600)
    _override_limiter(limiter)
    user_a = _signup(client, "a@example.com")
    user_b = _signup(client, "b@example.com")
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)

    spoofed = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(user_a["access_token"]),
        files=_pdf(),
        data={"user_id": str(user_b["user"]["id"]), "redis_key": "ratelimit:ai:1:0"},
    )
    second_a = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(user_a["access_token"]),
        files=_pdf(),
        data={"user_id": str(user_b["user"]["id"])},
    )
    first_b = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(user_b["access_token"]),
        files=_pdf(),
    )

    assert spoofed.status_code == 200
    assert second_a.status_code == 429
    assert first_b.status_code == 200
    assert "redis" not in second_a.text.lower()
    assert RATE_LIMIT_KEY_PREFIX not in second_a.text


def test_rate_limit_requires_authentication(client: TestClient) -> None:
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)
    response = client.post(ANALYSIS_PATH, files=_pdf())
    assert response.status_code == 401
    assert fake.calls == []


def test_provider_errors_still_map_after_allowed_rate_limit(client: TestClient) -> None:
    from app.services.ai_errors import AIProviderError

    backend = FakeRateLimitBackend()
    limiter = AIRateLimiter(backend, max_requests=10, window_seconds=3600)
    _override_limiter(limiter)
    tokens = _signup(client)
    fake = FakeAIClient(error=AIProviderError("The AI provider request failed."))
    _override_ai(fake)

    response = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        files=_pdf(),
    )
    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider request failed."
    assert "redis" not in response.text.lower()


def test_http_fail_open_when_redis_backend_fails(client: TestClient) -> None:
    limiter = AIRateLimiter(
        FakeRateLimitBackend(fail=True),
        max_requests=1,
        window_seconds=3600,
    )
    _override_limiter(limiter)
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)

    first = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        files=_pdf(),
    )
    second = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        files=_pdf(),
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert ResumeAnalysisResult.model_validate(first.json())
    assert "redis" not in first.text.lower()
    assert "localhost:6379" not in first.text
    assert "ConnectionError" not in first.text
