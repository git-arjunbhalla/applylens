from typing import Any

import pymupdf as fitz
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.api.deps import get_configured_ai_client
from app.main import app
from app.schemas.ai import RESUME_PDF_MAX_BYTES, ResumeAnalysisResult
from app.services.ai_client import parse_structured_json
from app.services.ai_errors import AIProviderError, AIResponseError, AITimeoutError
from app.services.resume_analysis import build_resume_analysis_prompt

SIGNUP_PATH = "/api/v1/auth/signup"
ANALYSIS_PATH = "/api/v1/ai/resume-analysis"
TEST_API_KEY = "test-ai-key-secret-must-not-leak"

VALID_RESUME = "Python developer with FastAPI and PostgreSQL experience at Acme."

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
    "keyword_suggestions": ["REST APIs", "SQL"],
    "improvement_suggestions": ["Add quantified results to the Acme role"],
    "rewrite_suggestions": [
        {
            "original": "Worked on backend services",
            "suggested": "Built FastAPI services backed by PostgreSQL",
            "reason": "Names tools already present in the resume",
        }
    ],
    "summary": "Solid technical resume with room for more concrete achievements.",
}

VALID_ANALYSIS_JSON = (
    '{"ats_score": 78, "score_breakdown": {"ats_compatibility": 80, '
    '"content_strength": 74, "keyword_optimization": 70, "resume_structure": 82, '
    '"achievement_quality": 68}, "strengths": [], "issues": [], "missing_sections": [], '
    '"detected_skills": [], "keyword_suggestions": [], "improvement_suggestions": [], '
    '"rewrite_suggestions": [], "summary": "ok"}'
)


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


def _make_pdf_bytes(text: str | None) -> bytes:
    document = fitz.open()
    page = document.new_page()
    if text:
        page.insert_text((72, 72), text)
    data = document.tobytes()
    document.close()
    return data


def _resume_file(
    data: bytes,
    filename: str = "resume.pdf",
    content_type: str = "application/pdf",
) -> dict:
    return {"resume": (filename, data, content_type)}


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


def _post_analysis(
    client: TestClient,
    *,
    access_token: str | None,
    files: dict | None,
) -> Any:
    headers = _auth_headers(access_token) if access_token else {}
    return client.post(ANALYSIS_PATH, headers=headers, files=files)


def test_resume_analysis_requires_authentication(client: TestClient) -> None:
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)

    response = _post_analysis(
        client,
        access_token=None,
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
    assert fake.calls == []


def test_resume_analysis_succeeds_with_mocked_client(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)

    response = _post_analysis(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 200
    body = response.json()
    assert body == VALID_ANALYSIS
    assert len(fake.calls) == 1
    prompt, schema = fake.calls[0]
    assert VALID_RESUME in prompt
    assert "JOB DESCRIPTION" not in prompt
    assert schema is ResumeAnalysisResult
    assert TEST_API_KEY not in response.text
    assert "api_key" not in body
    assert "AI_API_KEY" not in response.text


def test_resume_analysis_rejects_missing_pdf(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)

    response = client.post(
        ANALYSIS_PATH,
        headers=_auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 422
    assert fake.calls == []


def test_resume_analysis_rejects_non_pdf_upload(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)

    response = _post_analysis(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(b"just a resume", filename="resume.txt", content_type="text/plain"),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "The resume must be a PDF file."
    assert fake.calls == []


def test_resume_analysis_rejects_oversized_pdf(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)
    oversized = b"%PDF-1.4\n" + (b"x" * RESUME_PDF_MAX_BYTES)

    response = _post_analysis(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(oversized),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "The resume PDF must be 5 MB or smaller."
    assert fake.calls == []


def test_resume_analysis_rejects_corrupt_pdf(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)

    response = _post_analysis(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(b"%PDF-not-a-real-document"),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "The uploaded file is not a valid PDF."
    assert fake.calls == []


def test_resume_analysis_rejects_whitespace_only_pdf(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)

    response = _post_analysis(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes("   \n\t  ")),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "No extractable text was found in the PDF."
    assert fake.calls == []


def test_resume_analysis_timeout(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(error=AITimeoutError("The AI provider timed out."))
    _override_ai(fake)

    response = _post_analysis(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 504
    assert response.json()["detail"] == "The AI provider timed out."
    assert TEST_API_KEY not in response.text


def test_resume_analysis_rejects_pdf_with_no_extractable_text(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_ANALYSIS)
    _override_ai(fake)

    response = _post_analysis(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(None)),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "No extractable text was found in the PDF."
    assert fake.calls == []


def test_resume_analysis_provider_error(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(error=AIProviderError(f"upstream rejected {TEST_API_KEY}"))
    _override_ai(fake)

    response = _post_analysis(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider request failed."
    assert TEST_API_KEY not in response.text


def test_resume_analysis_malformed_json(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(raw="{not-json")
    _override_ai(fake)

    response = _post_analysis(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider returned an invalid response."
    assert TEST_API_KEY not in response.text


def test_resume_analysis_schema_validation_failure(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(raw='{"ats_score": 40}')
    _override_ai(fake)

    response = _post_analysis(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider returned an invalid response."


def test_resume_analysis_ats_score_out_of_range(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(raw=VALID_ANALYSIS_JSON.replace('"ats_score": 78', '"ats_score": 150'))
    _override_ai(fake)

    response = _post_analysis(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider returned an invalid response."


def test_resume_analysis_breakdown_score_out_of_range(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(
        raw=VALID_ANALYSIS_JSON.replace('"ats_compatibility": 80', '"ats_compatibility": -3'),
    )
    _override_ai(fake)

    response = _post_analysis(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 502


def test_resume_analysis_does_not_return_api_key_even_if_model_adds_extra_fields(
    client: TestClient,
) -> None:
    tokens = _signup(client)
    extra = {**VALID_ANALYSIS, "api_key": TEST_API_KEY, "provider_secret": TEST_API_KEY}
    fake = FakeAIClient(result=extra)
    _override_ai(fake)

    response = _post_analysis(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 200
    body = response.json()
    assert "api_key" not in body
    assert "provider_secret" not in body
    assert TEST_API_KEY not in response.text
    assert set(body) == {
        "ats_score",
        "score_breakdown",
        "strengths",
        "issues",
        "missing_sections",
        "detected_skills",
        "keyword_suggestions",
        "improvement_suggestions",
        "rewrite_suggestions",
        "summary",
    }
    assert set(body["score_breakdown"]) == {
        "ats_compatibility",
        "content_strength",
        "keyword_optimization",
        "resume_structure",
        "achievement_quality",
    }


def test_resume_analysis_response_error_is_mapped(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(error=AIResponseError("The AI provider returned invalid JSON."))
    _override_ai(fake)

    response = _post_analysis(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider returned an invalid response."


def test_prompt_is_standalone_and_not_jd_matching() -> None:
    prompt = build_resume_analysis_prompt(VALID_RESUME)

    assert VALID_RESUME in prompt
    assert "JOB DESCRIPTION" not in prompt
    assert "This task is NOT job-description matching" in prompt
    assert "Do not invent" in prompt
    assert "ats_score" in prompt
    assert "match_score" not in prompt
    assert "matching_skills" not in prompt
    assert "will pass an ATS" in prompt
