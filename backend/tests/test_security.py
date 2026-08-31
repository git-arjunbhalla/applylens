from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_is_not_plaintext() -> None:
    hashed = hash_password("password123")
    assert hashed != "password123"
    assert hashed.startswith("$2")


def test_verify_password_accepts_matching_secret() -> None:
    hashed = hash_password("correct-horse")
    assert verify_password("correct-horse", hashed) is True


def test_verify_password_rejects_wrong_secret() -> None:
    hashed = hash_password("correct-horse")
    assert verify_password("wrong-battery", hashed) is False


def test_password_hashes_are_salted() -> None:
    first = hash_password("password123")
    second = hash_password("password123")
    assert first != second
    assert verify_password("password123", first)
    assert verify_password("password123", second)


def test_access_token_round_trip() -> None:
    token = create_access_token(42)
    payload = decode_token(token, expected_type="access")
    assert payload["user_id"] == 42
    assert payload["type"] == "access"
    assert payload["sub"] == "42"


def test_refresh_token_round_trip() -> None:
    token = create_refresh_token(7)
    payload = decode_token(token, expected_type="refresh")
    assert payload["user_id"] == 7
    assert payload["type"] == "refresh"


def test_decode_rejects_expired_access_token() -> None:
    token = create_access_token(1, expires_delta=timedelta(seconds=-1))
    try:
        decode_token(token, expected_type="access")
        raise AssertionError("expected TokenError")
    except TokenError as exc:
        assert exc.detail == "Token has expired"


def test_decode_rejects_invalid_token() -> None:
    try:
        decode_token("not-a-jwt", expected_type="access")
        raise AssertionError("expected TokenError")
    except TokenError as exc:
        assert exc.detail == "Invalid token"


def test_decode_rejects_wrong_token_type() -> None:
    refresh = create_refresh_token(1)
    try:
        decode_token(refresh, expected_type="access")
        raise AssertionError("expected TokenError")
    except TokenError as exc:
        assert exc.detail == "Invalid token type"


def test_decode_rejects_token_signed_with_wrong_secret() -> None:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "1",
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        "this-is-not-the-server-secret-and-is-32b+",
        algorithm=settings.jwt_algorithm,
    )
    try:
        decode_token(token, expected_type="access")
        raise AssertionError("expected TokenError")
    except TokenError as exc:
        assert exc.detail == "Invalid token"


def test_decode_rejects_missing_subject() -> None:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    try:
        decode_token(token, expected_type="access")
        raise AssertionError("expected TokenError")
    except TokenError as exc:
        assert exc.detail == "Token is missing required claims"


def test_decode_rejects_non_integer_subject() -> None:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "not-an-id",
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    try:
        decode_token(token, expected_type="access")
        raise AssertionError("expected TokenError")
    except TokenError as exc:
        assert exc.detail == "Token is missing required claims"


def test_token_error_messages_do_not_include_signing_secret() -> None:
    try:
        decode_token("garbage", expected_type="access")
    except TokenError as exc:
        assert settings.jwt_secret not in exc.detail
        assert settings.jwt_secret not in str(exc)
