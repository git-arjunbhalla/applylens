from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import bcrypt
import jwt

from app.core.config import settings

TokenType = Literal["access", "refresh"]


class TokenError(Exception):
    """Raised when a JWT fails signature, expiry, type, or claim checks."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_token(
    *,
    user_id: int,
    token_type: TokenType,
    expires_delta: timedelta,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    delta = expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    return create_token(user_id=user_id, token_type="access", expires_delta=delta)


def create_refresh_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    delta = expires_delta or timedelta(days=settings.jwt_refresh_token_expire_days)
    return create_token(user_id=user_id, token_type="refresh", expires_delta=delta)


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Invalid token") from exc

    if payload.get("type") != expected_type:
        raise TokenError("Invalid token type")

    subject = payload.get("sub")
    if subject is None:
        raise TokenError("Token is missing required claims")

    try:
        payload["user_id"] = int(subject)
    except (TypeError, ValueError) as exc:
        raise TokenError("Token is missing required claims") from exc

    return payload
