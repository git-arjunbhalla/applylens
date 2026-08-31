from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenError, decode_token
from app.db.session import get_db
from app.models.user import User
from app.services.ai_client import AIClient, get_ai_client
from app.services.ai_errors import AIError
from app.services.auth import get_user_by_id
from app.services.rate_limit import (
    AI_RATE_LIMIT_DETAIL,
    AIRateLimiter,
    get_ai_rate_limiter,
)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await get_user_by_id(db, payload["user_id"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def enforce_ai_rate_limit(
    current_user: Annotated[User, Depends(get_current_user)],
    limiter: Annotated[AIRateLimiter, Depends(get_ai_rate_limiter)],
) -> User:
    """Consume one AI quota unit for the authenticated user. Runs after auth."""
    decision = await limiter.hit(current_user.id)
    if not decision.allowed:
        headers: dict[str, str] = {}
        if decision.retry_after_seconds > 0:
            headers["Retry-After"] = str(decision.retry_after_seconds)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=AI_RATE_LIMIT_DETAIL,
            headers=headers,
        )
    return current_user


def get_configured_ai_client() -> AIClient:
    """Resolve the Stage 10 provider. Route handlers must not import Gemini."""
    try:
        return get_ai_client()
    except AIError as exc:
        from app.api.ai_http import http_exception_from_ai_error

        raise http_exception_from_ai_error(exc) from exc
