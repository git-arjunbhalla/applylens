from fastapi import HTTPException, status

from app.services.ai_errors import (
    AIConfigurationError,
    AIError,
    AIProviderError,
    AIResponseError,
    AITimeoutError,
    AIUnsupportedProviderError,
)


def http_exception_from_ai_error(exc: AIError) -> HTTPException:
    """Map provider errors to consistent API errors without leaking credentials."""
    if isinstance(exc, (AIConfigurationError, AIUnsupportedProviderError)):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI service is not configured.",
        )
    if isinstance(exc, AITimeoutError):
        return HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The AI provider timed out.",
        )
    if isinstance(exc, AIResponseError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI provider returned an invalid response.",
        )
    if isinstance(exc, AIProviderError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI provider request failed.",
        )
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="The AI request failed.",
    )
