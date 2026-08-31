from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token

SIGNUP_PATH = "/api/v1/auth/signup"
LOGIN_PATH = "/api/v1/auth/login"
REFRESH_PATH = "/api/v1/auth/refresh"
ME_PATH = "/api/v1/auth/me"


def _signup(
    client: TestClient,
    email: str = "user@example.com",
    password: str = "password123",
):
    return client.post(SIGNUP_PATH, json={"email": email, "password": password})


def test_signup_creates_user_and_returns_tokens(client: TestClient) -> None:
    response = _signup(client)

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["email"] == "user@example.com"
    assert "hashed_password" not in body["user"]
    assert "password" not in body["user"]

    access_payload = decode_token(body["access_token"], expected_type="access")
    refresh_payload = decode_token(body["refresh_token"], expected_type="refresh")
    assert access_payload["user_id"] == body["user"]["id"]
    assert refresh_payload["user_id"] == body["user"]["id"]


def test_duplicate_signup_is_rejected(client: TestClient) -> None:
    first = _signup(client)
    assert first.status_code == 201

    duplicate = _signup(client)
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "An account with this email already exists"


def test_signup_normalizes_email_for_uniqueness(client: TestClient) -> None:
    assert _signup(client, email="User@Example.com").status_code == 201
    duplicate = _signup(client, email="user@example.com")
    assert duplicate.status_code == 409


def test_login_returns_tokens(client: TestClient) -> None:
    _signup(client)
    response = client.post(
        LOGIN_PATH,
        json={"email": "user@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "user@example.com"
    decode_token(body["access_token"], expected_type="access")
    decode_token(body["refresh_token"], expected_type="refresh")


def test_login_rejects_incorrect_password(client: TestClient) -> None:
    _signup(client)
    response = client.post(
        LOGIN_PATH,
        json={"email": "user@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_rejects_unknown_email(client: TestClient) -> None:
    response = client.post(
        LOGIN_PATH,
        json={"email": "missing@example.com", "password": "password123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_protected_route_accepts_valid_access_token(client: TestClient) -> None:
    signup = _signup(client).json()
    response = client.get(
        ME_PATH,
        headers={"Authorization": f"Bearer {signup['access_token']}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "user@example.com"
    assert body["id"] == signup["user"]["id"]
    assert "hashed_password" not in body


def test_protected_route_rejects_missing_token(client: TestClient) -> None:
    response = client.get(ME_PATH)

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_protected_route_rejects_invalid_token(client: TestClient) -> None:
    response = client.get(
        ME_PATH,
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_protected_route_rejects_refresh_token(client: TestClient) -> None:
    signup = _signup(client).json()
    response = client.get(
        ME_PATH,
        headers={"Authorization": f"Bearer {signup['refresh_token']}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token type"


def test_protected_route_rejects_expired_access_token(client: TestClient) -> None:
    signup = _signup(client).json()
    expired = create_access_token(signup["user"]["id"], expires_delta=timedelta(seconds=-1))
    response = client.get(
        ME_PATH,
        headers={"Authorization": f"Bearer {expired}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"


def test_refresh_issues_new_tokens(client: TestClient) -> None:
    signup = _signup(client).json()
    response = client.post(REFRESH_PATH, json={"refresh_token": signup["refresh_token"]})

    assert response.status_code == 200
    body = response.json()
    decode_token(body["access_token"], expected_type="access")
    decode_token(body["refresh_token"], expected_type="refresh")

    me = client.get(
        ME_PATH,
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"


def test_refresh_rejects_access_token(client: TestClient) -> None:
    signup = _signup(client).json()
    response = client.post(REFRESH_PATH, json={"refresh_token": signup["access_token"]})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token type"


def test_refresh_rejects_expired_refresh_token(client: TestClient) -> None:
    signup = _signup(client).json()
    expired = create_refresh_token(signup["user"]["id"], expires_delta=timedelta(seconds=-1))
    response = client.post(REFRESH_PATH, json={"refresh_token": expired})

    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"


def test_refresh_rejects_invalid_token(client: TestClient) -> None:
    response = client.post(REFRESH_PATH, json={"refresh_token": "not-a-real-token"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_signup_rejects_invalid_email_and_short_password(client: TestClient) -> None:
    invalid_email = client.post(
        SIGNUP_PATH,
        json={"email": "not-an-email", "password": "password123"},
    )
    short_password = client.post(
        SIGNUP_PATH,
        json={"email": "user@example.com", "password": "short"},
    )
    missing = client.post(SIGNUP_PATH, json={"email": "user@example.com"})

    assert invalid_email.status_code == 422
    assert short_password.status_code == 422
    assert missing.status_code == 422


def test_protected_route_rejects_malformed_authorization_header(client: TestClient) -> None:
    signup = _signup(client).json()

    missing_scheme = client.get(ME_PATH, headers={"Authorization": signup["access_token"]})
    basic = client.get(ME_PATH, headers={"Authorization": f"Basic {signup['access_token']}"})
    empty_bearer = client.get(ME_PATH, headers={"Authorization": "Bearer"})

    for response in (missing_scheme, basic, empty_bearer):
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
        assert "hashed_password" not in response.text
        assert settings.jwt_secret not in response.text


def test_protected_route_rejects_token_signed_with_wrong_secret(client: TestClient) -> None:
    signup = _signup(client).json()
    now = datetime.now(timezone.utc)
    forged = jwt.encode(
        {
            "sub": str(signup["user"]["id"]),
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        "forged-signing-secret-must-be-32-bytes+",
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(ME_PATH, headers={"Authorization": f"Bearer {forged}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"
    assert "forged-signing-secret" not in response.text


def test_refresh_rejects_token_for_unknown_user(client: TestClient) -> None:
    orphan = create_refresh_token(999_999)
    response = client.post(REFRESH_PATH, json={"refresh_token": orphan})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"
