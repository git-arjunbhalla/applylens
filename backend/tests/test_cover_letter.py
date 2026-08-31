from typing import Any

import pymupdf as fitz
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.api.deps import get_configured_ai_client
from app.main import app
from app.schemas.ai import CoverLetterResult, RESUME_PDF_MAX_BYTES
from app.services.ai_client import parse_structured_json
from app.services.ai_errors import AIProviderError, AIResponseError, AITimeoutError
from app.services.cover_letter import build_cover_letter_prompt

SIGNUP_PATH = "/api/v1/auth/signup"
COVER_LETTER_PATH = "/api/v1/ai/cover-letter"
TEST_API_KEY = "test-ai-key-secret-must-not-leak"

VALID_RESUME = "Jane Doe. Python developer with FastAPI and PostgreSQL experience."
VALID_JD = "Looking for a Python engineer with FastAPI and PostgreSQL."
VALID_COMPANY = "Acme Labs"
VALID_ROLE = "Backend Engineer"

VALID_LETTER = (
    "Dear Hiring Manager,\n\n"
    "I am applying for the Backend Engineer role at Acme Labs. "
    "My resume includes Python, FastAPI, and PostgreSQL experience.\n\n"
    "Sincerely,\nJane Doe"
)

VALID_RESULT = {"cover_letter": VALID_LETTER}


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


def _form_data(
    *,
    job_description: str | None = VALID_JD,
    company: str | None = VALID_COMPANY,
    role: str | None = VALID_ROLE,
) -> dict[str, str] | None:
    data: dict[str, str] = {}
    if job_description is not None:
        data["job_description"] = job_description
    if company is not None:
        data["company"] = company
    if role is not None:
        data["role"] = role
    return data or None


def _post_cover_letter(
    client: TestClient,
    *,
    access_token: str | None,
    files: dict | None,
    job_description: str | None = VALID_JD,
    company: str | None = VALID_COMPANY,
    role: str | None = VALID_ROLE,
) -> Any:
    headers = _auth_headers(access_token) if access_token else {}
    return client.post(
        COVER_LETTER_PATH,
        headers=headers,
        files=files,
        data=_form_data(
            job_description=job_description,
            company=company,
            role=role,
        ),
    )


def test_cover_letter_requires_authentication(client: TestClient) -> None:
    fake = FakeAIClient(result=VALID_RESULT)
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=None,
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
    assert fake.calls == []


def test_cover_letter_succeeds_with_mocked_client(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_RESULT)
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 200
    body = response.json()
    assert body == VALID_RESULT
    assert len(fake.calls) == 1
    prompt, schema = fake.calls[0]
    assert VALID_RESUME in prompt
    assert VALID_JD in prompt
    assert VALID_COMPANY in prompt
    assert VALID_ROLE in prompt
    assert schema is CoverLetterResult
    assert TEST_API_KEY not in response.text
    assert "api_key" not in body
    assert "AI_API_KEY" not in response.text


def test_cover_letter_strips_form_fields(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_RESULT)
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
        job_description=f"\n{VALID_JD}\n",
        company=f"  {VALID_COMPANY}  ",
        role=f" {VALID_ROLE} ",
    )

    assert response.status_code == 200
    assert response.json()["cover_letter"] == VALID_LETTER
    prompt, _schema = fake.calls[0]
    assert VALID_COMPANY in prompt
    assert VALID_ROLE in prompt


def test_cover_letter_rejects_missing_pdf(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_RESULT)
    _override_ai(fake)

    response = client.post(
        COVER_LETTER_PATH,
        headers=_auth_headers(tokens["access_token"]),
        data=_form_data(),
    )

    assert response.status_code == 422
    assert fake.calls == []


def test_cover_letter_rejects_missing_company(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_RESULT)
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
        company=None,
    )

    assert response.status_code == 422
    assert fake.calls == []


def test_cover_letter_rejects_missing_role(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_RESULT)
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
        role=None,
    )

    assert response.status_code == 422
    assert fake.calls == []


def test_cover_letter_rejects_non_pdf_upload(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_RESULT)
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(b"just a resume", filename="resume.txt", content_type="text/plain"),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "The resume must be a PDF file."
    assert fake.calls == []


def test_cover_letter_rejects_empty_job_description(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_RESULT)
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
        job_description="",
    )

    assert response.status_code == 422
    assert fake.calls == []


def test_cover_letter_rejects_blank_company(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_RESULT)
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
        company="   ",
    )

    assert response.status_code == 422
    assert fake.calls == []


def test_cover_letter_rejects_blank_role(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_RESULT)
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
        role="\n",
    )

    assert response.status_code == 422
    assert fake.calls == []


def test_cover_letter_rejects_oversized_pdf(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_RESULT)
    _override_ai(fake)
    oversized = b"%PDF-1.4\n" + (b"x" * RESUME_PDF_MAX_BYTES)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(oversized),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "The resume PDF must be 5 MB or smaller."
    assert fake.calls == []


def test_cover_letter_rejects_pdf_with_no_extractable_text(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(result=VALID_RESULT)
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(None)),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "No extractable text was found in the PDF."
    assert fake.calls == []


def test_cover_letter_provider_error(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(error=AIProviderError(f"upstream rejected {TEST_API_KEY}"))
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider request failed."
    assert TEST_API_KEY not in response.text


def test_cover_letter_timeout(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(error=AITimeoutError("The AI provider timed out."))
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 504
    assert response.json()["detail"] == "The AI provider timed out."


def test_cover_letter_malformed_json(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(raw="{not-json")
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider returned an invalid response."
    assert TEST_API_KEY not in response.text


def test_cover_letter_schema_validation_failure(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(raw='{"summary": "not a letter"}')
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider returned an invalid response."


def test_cover_letter_blank_letter_is_rejected(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(raw='{"cover_letter": "   "}')
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider returned an invalid response."


def test_cover_letter_does_not_return_api_key_even_if_model_adds_extra_fields(
    client: TestClient,
) -> None:
    tokens = _signup(client)
    extra = {**VALID_RESULT, "api_key": TEST_API_KEY, "provider_secret": TEST_API_KEY}
    fake = FakeAIClient(result=extra)
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 200
    body = response.json()
    assert "api_key" not in body
    assert "provider_secret" not in body
    assert TEST_API_KEY not in response.text
    assert set(body) == {"cover_letter"}


def test_cover_letter_response_error_is_mapped(client: TestClient) -> None:
    tokens = _signup(client)
    fake = FakeAIClient(error=AIResponseError("The AI provider returned invalid JSON."))
    _override_ai(fake)

    response = _post_cover_letter(
        client,
        access_token=tokens["access_token"],
        files=_resume_file(_make_pdf_bytes(VALID_RESUME)),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "The AI provider returned an invalid response."


def test_prompt_includes_inputs_and_no_fabrication_rules() -> None:
    prompt = build_cover_letter_prompt(VALID_RESUME, VALID_JD, VALID_COMPANY, VALID_ROLE)

    assert VALID_RESUME in prompt
    assert VALID_JD in prompt
    assert VALID_COMPANY in prompt
    assert VALID_ROLE in prompt
    assert "Do not invent" in prompt
    assert "cover_letter" in prompt
