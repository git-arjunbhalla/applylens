from fastapi.testclient import TestClient

from app.core.config import settings


def test_cors_allows_configured_origin(client: TestClient) -> None:
    origin = settings.cors_origin_list[0]
    response = client.get("/health", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin


def test_cors_does_not_reflect_unknown_origin(client: TestClient) -> None:
    response = client.get(
        "/health",
        headers={"Origin": "https://evil.example"},
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") != "https://evil.example"


def test_cors_preflight_for_authenticated_api(client: TestClient) -> None:
    origin = settings.cors_origin_list[0]
    response = client.options(
        "/api/v1/applications",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code in {200, 204}
    assert response.headers.get("access-control-allow-origin") == origin
    allow_headers = response.headers.get("access-control-allow-headers", "").lower()
    assert "authorization" in allow_headers
