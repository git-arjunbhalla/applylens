from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, ValidationError

from app.core.config import Settings, get_settings
from app.services.ai_errors import (
    AIConfigurationError,
    AIError,
    AIProviderError,
    AIResponseError,
    AITimeoutError,
    AIUnsupportedProviderError,
)

SUPPORTED_PROVIDERS = frozenset({"gemini"})


def parse_structured_json(
    raw: Any,
    schema: type[BaseModel] | None = None,
) -> dict[str, Any]:
    """Parse provider text as JSON and optionally validate it with Pydantic."""
    if raw is None:
        raise AIResponseError("The AI provider returned an empty response.")
    if not isinstance(raw, str):
        raise AIResponseError("The AI provider returned an unexpected response format.")

    text = _strip_json_fences(raw.strip())
    if not text:
        raise AIResponseError("The AI provider returned an empty response.")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AIResponseError("The AI provider returned invalid JSON.") from exc

    if schema is None:
        if not isinstance(data, dict):
            raise AIResponseError("The AI provider returned JSON that was not an object.")
        return data

    try:
        validated = schema.model_validate(data)
    except ValidationError as exc:
        raise AIResponseError(
            "The AI response did not match the expected structure."
        ) from exc
    return validated.model_dump()


def _strip_json_fences(text: str) -> str:
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


class AIClient(ABC):
    """Provider-agnostic AI client used by later FastAPI AI endpoints."""

    provider_name: str

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        """Return model text for a prompt."""

    def generate_json(
        self,
        prompt: str,
        schema: type[BaseModel] | None = None,
    ) -> dict[str, Any]:
        """Return validated JSON from the provider."""
        return parse_structured_json(self.generate_text(prompt), schema=schema)


class GeminiProvider(AIClient):
    provider_name = "gemini"

    def __init__(
        self,
        *,
        model: str,
        timeout_seconds: float,
        api_key: str | None = None,
        client: Any | None = None,
    ) -> None:
        self._model = model
        if client is not None:
            self._client = client
            return
        if not api_key:
            raise AIConfigurationError("AI_API_KEY is not configured.")
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=int(timeout_seconds * 1000)),
        )

    def generate_text(self, prompt: str) -> str:
        text = self._complete(prompt, json_mode=False)
        if not text.strip():
            raise AIResponseError("The AI provider returned an empty response.")
        return text

    def generate_json(
        self,
        prompt: str,
        schema: type[BaseModel] | None = None,
    ) -> dict[str, Any]:
        text = self._complete(prompt, json_mode=True, schema=schema)
        return parse_structured_json(text, schema=schema)

    def _complete(
        self,
        prompt: str,
        *,
        json_mode: bool,
        schema: type[BaseModel] | None = None,
    ) -> str:
        config: dict[str, Any] | None = None
        if json_mode:
            config = {"response_mime_type": "application/json"}
            if schema is not None:
                config["response_schema"] = schema

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
        except (httpx.TimeoutException, TimeoutError) as exc:
            raise AITimeoutError("The AI provider timed out.") from exc
        except genai_errors.APIError as exc:
            raise AIProviderError("The AI provider request failed.") from exc
        except AIError:
            raise
        except Exception as exc:
            raise AIProviderError("The AI provider request failed.") from exc

        text = getattr(response, "text", None)
        if text is None:
            return ""
        if not isinstance(text, str):
            raise AIResponseError("The AI provider returned an unexpected response format.")
        return text


def get_ai_client(app_settings: Settings | None = None) -> AIClient:
    """Build the configured provider. FastAPI handlers should call this, not Gemini."""
    cfg = app_settings or get_settings()
    provider = cfg.ai_provider.strip().lower()
    if not provider:
        raise AIConfigurationError("AI_PROVIDER is not configured.")
    if provider not in SUPPORTED_PROVIDERS:
        raise AIUnsupportedProviderError(f"Unsupported AI provider: {provider}")

    api_key = cfg.ai_api_key_value
    if not api_key:
        raise AIConfigurationError("AI_API_KEY is not configured.")

    if provider == "gemini":
        return GeminiProvider(
            api_key=api_key,
            model=cfg.ai_model,
            timeout_seconds=cfg.ai_timeout_seconds,
        )

    raise AIUnsupportedProviderError(f"Unsupported AI provider: {provider}")
