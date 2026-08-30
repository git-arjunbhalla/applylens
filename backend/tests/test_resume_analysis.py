from typing import Any

from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.api.deps import get_configured_ai_client
from app.main import app
from app.schemas.ai import ResumeAnalysisResult
from app.services.ai_client import parse_structured_json
from app.services.ai_errors import AIProviderError, AIResponseError
from app.services.resume_analysis import build_resume_analysis_prompt

SIGNUP_PATH = "/api/v1/auth/signup"
ANALYSIS_PATH = "/api/v1/ai/resume-analysis"
TEST_API_KEY = "test-ai-key-secret-must-not-leak"

VALID_RESUME = "Python developer with FastAPI and PostgreSQL experience."
VALID_JD = "Looking for a Python engineer with FastAPI, PostgreSQL, and React."

VALID_ANALYSIS = {
    "match_score": 72,
    "matching_skills": ["Python", "FastAPI", "PostgreSQL"],
    "missing_skills": ["React"],
    "strengths": ["Backend Python experience"],
    "weaknesses": ["No frontend evidence"],
    "recommendations": ["Add React projects if you have them"],
}


class FakeAIClient:
    def __init__(
        self,
        *,
        result: dict[str, Any] | None = None,
        raw: str | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.raw = raw
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
        if self.raw is not None:
            return parse_structured_json(self.raw, schema=schema)
        assert self.result is not None
        if schema is not None:
            return schema.model_validate(self.result).model_dump()
        return self.result


def _signup(client: TestClient) -> dict:
    response = client.post(
        SIGNUP_PATH,
        json={"email": "user@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    return response.json()


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _override_ai(fake: FakeAIClient) -> None:
    app.dependency_overrides[get_configured_ai_client] = lambda: fake


def test_resume_analysis_requires_authentication(client: TestClient) -> None:
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)

    response = client.post(
        ANALYSIS_PATH,
        json={"resume_text": VALID_RESUME, "job_description": VALID_JD},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
    assert fake.calls == []


def test_resume_analysis_succeeds_with_mocked_client(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)

    response = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        json={"resume_text": VALID_RESUME, "job_description": VALID_JD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body == VALID_ANALYSIS
    assert len(fake.calls) == 1
    prompt, schema = fake.calls[0]
    assert VALID_RESUME in prompt
    assert VALID_JD in prompt
    assert schema is ResumeAnalysisResult
    assert TEST_API_KEY not in response.text
    assert "api_key" not in body
    assert "AI_API_KEY" not in response.text


def test_resume_analysis_accepts_valid_resume_and_jd(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)

    response = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        json={"resume_text": f"  {VALID_RESUME}  ", "job_description": f"\n{VALID_JD}\n"},
    )

    assert response.status_code == 200
    assert response.json()["match_score"] == 72
    assert response.json()["matching_skills"] == ["Python", "FastAPI", "PostgreSQL"]
    assert response.json()["missing_skills"] == ["React"]
    assert response.json()["strengths"]
    assert response.json()["weaknesses"]
    assert response.json()["recommendations"]


def test_resume_analysis_rejects_missing_fields(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)

    response = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        json={"resume_text": VALID_RESUME},
    )

    assert response.status_code == 422
    assert fake.calls == []


def test_resume_analysis_rejects_empty_input(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)

    response = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        json={"resume_text": "   ", "job_description": VALID_JD},
    )

    assert response.status_code == 422
    assert fake.calls == []

    response = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        json={"resume_text": VALID_RESUME, "job_description": ""},
    )

    assert response.status_code == 422
    assert fake.calls == []


def test_resume_analysis_provider_error(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(error=AIProviderError(f"upstream rejected {TEST_API_KEY}"))
    _override_ai(fake)

    response = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        json={"resume_text": VALID_RESUME, "job_description": VALID_JD},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider request failed."
    assert TEST_API_KEY not in response.text


def test_resume_analysis_malformed_json(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(raw="{not-json")
    _override_ai(fake)

    response = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        json={"resume_text": VALID_RESUME, "job_description": VALID_JD},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider returned an invalid response."
    assert TEST_API_KEY not in response.text


def test_resume_analysis_schema_validation_failure(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(raw='{"match_score": 40}')
    _override_ai(fake)

    response = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        json={"resume_text": VALID_RESUME, "job_description": VALID_JD},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider returned an invalid response."


def test_resume_analysis_match_score_out_of_range(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(
        raw='{"match_score": 150, "matching_skills": [], "missing_skills": [], '
        '"strengths": [], "weaknesses": [], "recommendations": []}',
    )
    _override_ai(fake)

    response = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        json={"resume_text": VALID_RESUME, "job_description": VALID_JD},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider returned an invalid response."


def test_resume_analysis_match_score_negative_is_rejected(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(
        raw='{"match_score": -1, "matching_skills": [], "missing_skills": [], '
        '"strengths": [], "weaknesses": [], "recommendations": []}',
    )
    _override_ai(fake)

    response = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        json={"resume_text": VALID_RESUME, "job_description": VALID_JD},
    )

    assert response.status_code == 502


def test_resume_analysis_does_not_return_api_key_even_if_model_adds_extra_fields(
    client: TestClient,
) -> None:
    tokens = _signup(client)
    extra = {**VALID_ANALYSIS, "api_key": TEST_API_KEY, "provider_secret": TEST_API_KEY}
    fake = FakeAIClient(result=extra)
    _override_ai(fake)

    response = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        json={"resume_text": VALID_RESUME, "job_description": VALID_JD},
    )

    assert response.status_code == 200
    body = response.json()
    assert "api_key" not in body
    assert "provider_secret" not in body
    assert TEST_API_KEY not in response.text
    assert set(body) == {
        "match_score",
        "matching_skills",
        "missing_skills",
        "strengths",
        "weaknesses",
        "recommendations",
    }


def test_resume_analysis_response_error_is_mapped(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(error=AIResponseError("The AI provider returned invalid JSON."))
    _override_ai(fake)

    response = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        json={"resume_text": VALID_RESUME, "job_description": VALID_JD},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider returned an invalid response."


def test_prompt_includes_inputs_and_no_fabrication_rules() -> None:
    prompt = build_resume_analysis_prompt(VALID_RESUME, VALID_JD)

    assert VALID_RESUME in prompt
    assert VALID_JD in prompt
    assert "Do not invent" in prompt
    assert "match_score" in prompt
    assert "matching_skills" in prompt
