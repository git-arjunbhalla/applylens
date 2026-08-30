import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from google.genai import errors as genai_errors
from pydantic import BaseModel, SecretStr

from app.core.config import Settings
from app.services.ai_client import (
    GeminiProvider,
    get_ai_client,
    parse_structured_json,
)
from app.services.ai_errors import (
    AIConfigurationError,
    AIProviderError,
    AIResponseError,
    AITimeoutError,
    AIUnsupportedProviderError,
)

TEST_API_KEY = "test-ai-key-secret"


class SamplePayload(BaseModel):
    label: str
    score: int


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "ai_provider": "gemini",
        "ai_api_key": TEST_API_KEY,
        "ai_model": "gemini-2.5-flash",
        "ai_timeout_seconds": 30.0,
    }
    values.update(overrides)
    return Settings(**values)


def _client_returning(text: object) -> MagicMock:
    client = MagicMock()
    client.models.generate_content.return_value = SimpleNamespace(text=text)
    return client


def _client_raising(exc: Exception) -> MagicMock:
    client = MagicMock()
    client.models.generate_content.side_effect = exc
    return client


def test_settings_expose_ai_configuration() -> None:
    settings = _settings()

    assert settings.ai_provider == "gemini"
    assert settings.ai_api_key_value == TEST_API_KEY
    assert "test-ai-key-secret" not in repr(settings.ai_api_key)


def test_secret_str_does_not_print_api_key() -> None:
    settings = Settings(ai_api_key=SecretStr(TEST_API_KEY))
    assert TEST_API_KEY not in str(settings.ai_api_key)
    assert TEST_API_KEY not in repr(settings)


def test_get_ai_client_selects_gemini() -> None:
    client = get_ai_client(_settings())

    assert isinstance(client, GeminiProvider)
    assert client.provider_name == "gemini"


def test_unsupported_provider_is_rejected() -> None:
    with pytest.raises(AIUnsupportedProviderError, match="openai"):
        get_ai_client(_settings(ai_provider="openai"))


def test_missing_api_key_is_rejected() -> None:
    with pytest.raises(AIConfigurationError, match="AI_API_KEY"):
        get_ai_client(_settings(ai_api_key=""))


def test_blank_provider_is_rejected() -> None:
    with pytest.raises(AIConfigurationError, match="AI_PROVIDER"):
        get_ai_client(_settings(ai_provider="   "))


def test_generate_text_success_uses_injected_client() -> None:
    provider = GeminiProvider(
        model="gemini-2.5-flash",
        timeout_seconds=5,
        client=_client_returning("plain text reply"),
    )

    assert provider.generate_text("hello") == "plain text reply"


def test_generate_json_success_parses_object() -> None:
    provider = GeminiProvider(
        model="gemini-2.5-flash",
        timeout_seconds=5,
        client=_client_returning('{"label": "fit", "score": 8}'),
    )

    result = provider.generate_json("score this", schema=SamplePayload)

    assert result == {"label": "fit", "score": 8}
    provider._client.models.generate_content.assert_called_once()
    kwargs = provider._client.models.generate_content.call_args.kwargs
    assert kwargs["config"]["response_mime_type"] == "application/json"
    assert kwargs["config"]["response_schema"] is SamplePayload


def test_timeout_becomes_ai_timeout_error() -> None:
    provider = GeminiProvider(
        model="gemini-2.5-flash",
        timeout_seconds=5,
        client=_client_raising(httpx.TimeoutException("request timed out")),
    )

    with pytest.raises(AITimeoutError, match="timed out"):
        provider.generate_text("hello")


def test_provider_api_error_is_wrapped() -> None:
    api_error = genai_errors.APIError(
        code=503,
        response_json={"error": {"message": "unavailable"}},
        response=None,
    )
    provider = GeminiProvider(
        model="gemini-2.5-flash",
        timeout_seconds=5,
        client=_client_raising(api_error),
    )

    with pytest.raises(AIProviderError, match="request failed"):
        provider.generate_text("hello")


def test_generic_provider_failure_is_wrapped() -> None:
    provider = GeminiProvider(
        model="gemini-2.5-flash",
        timeout_seconds=5,
        client=_client_raising(RuntimeError(f"upstream rejected {TEST_API_KEY}")),
    )

    with pytest.raises(AIProviderError) as exc_info:
        provider.generate_text("hello")

    assert TEST_API_KEY not in str(exc_info.value)
    assert TEST_API_KEY not in exc_info.value.args[0]


def test_empty_response_is_rejected() -> None:
    provider = GeminiProvider(
        model="gemini-2.5-flash",
        timeout_seconds=5,
        client=_client_returning("   "),
    )

    with pytest.raises(AIResponseError, match="empty"):
        provider.generate_text("hello")


def test_malformed_json_is_rejected() -> None:
    provider = GeminiProvider(
        model="gemini-2.5-flash",
        timeout_seconds=5,
        client=_client_returning("{not-json"),
    )

    with pytest.raises(AIResponseError, match="invalid JSON"):
        provider.generate_json("hello")


def test_json_array_without_schema_is_rejected() -> None:
    with pytest.raises(AIResponseError, match="not an object"):
        parse_structured_json("[1, 2]")


def test_unexpected_response_type_is_rejected() -> None:
    with pytest.raises(AIResponseError, match="unexpected"):
        parse_structured_json({"label": "x"})


def test_missing_structured_fields_are_rejected() -> None:
    with pytest.raises(AIResponseError, match="expected structure"):
        parse_structured_json('{"label": "only"}', schema=SamplePayload)


def test_fenced_json_is_accepted() -> None:
    raw = '```json\n{"label": "ok", "score": 3}\n```'
    assert parse_structured_json(raw, schema=SamplePayload) == {"label": "ok", "score": 3}


def test_none_response_is_rejected() -> None:
    with pytest.raises(AIResponseError, match="empty"):
        parse_structured_json(None)


@pytest.mark.skipif(
    os.getenv("APPLYLENS_LIVE_GEMINI") != "1",
    reason="Optional live Gemini check; set APPLYLENS_LIVE_GEMINI=1 to run.",
)
def test_live_gemini_generate_json_optional() -> None:
    client = get_ai_client()
    result = client.generate_json(
        'Return JSON {"label": "ping", "score": 1} and nothing else.',
        schema=SamplePayload,
    )
    assert "label" in result
    assert "score" in result
