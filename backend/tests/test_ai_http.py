from pathlib import Path

from app.api.ai_http import http_exception_from_ai_error
from app.services.ai_errors import (
    AIConfigurationError,
    AIError,
    AIProviderError,
    AIResponseError,
    AITimeoutError,
    AIUnsupportedProviderError,
)

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_configuration_error_is_503_without_secret_names() -> None:
    mapped = http_exception_from_ai_error(AIConfigurationError("AI_API_KEY is missing"))
    assert mapped.status_code == 503
    assert mapped.detail == "The AI service is not configured."
    assert "AI_API_KEY" not in mapped.detail


def test_unsupported_provider_is_503() -> None:
    mapped = http_exception_from_ai_error(AIUnsupportedProviderError("openai"))
    assert mapped.status_code == 503
    assert mapped.detail == "The AI service is not configured."


def test_timeout_is_504() -> None:
    mapped = http_exception_from_ai_error(AITimeoutError("deadline exceeded at gemini"))
    assert mapped.status_code == 504
    assert mapped.detail == "The AI provider timed out."
    assert "gemini" not in mapped.detail.lower()


def test_response_and_provider_errors_are_502() -> None:
    response = http_exception_from_ai_error(AIResponseError("invalid JSON from vendor"))
    provider = http_exception_from_ai_error(AIProviderError("503 unavailable redis://localhost"))
    assert response.status_code == 502
    assert response.detail == "The AI provider returned an invalid response."
    assert provider.status_code == 502
    assert provider.detail == "The AI provider request failed."
    assert "redis" not in provider.detail.lower()


def test_unknown_ai_error_is_generic_502() -> None:
    mapped = http_exception_from_ai_error(AIError("internal stack"))
    assert mapped.status_code == 502
    assert mapped.detail == "The AI request failed."


def test_gemini_sdk_is_only_imported_by_backend_ai_client() -> None:
    hits: list[Path] = []
    for path in (BACKEND_DIR / "app").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "from google" in text or "import google" in text:
            hits.append(path)
    assert hits == [BACKEND_DIR / "app" / "services" / "ai_client.py"]
