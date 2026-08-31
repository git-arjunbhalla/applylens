"""Explicit User A vs User B ownership checks.

These overlap some CRUD tests on purpose: authorization must be proven
independently of happy-path coverage.
"""

from fastapi.testclient import TestClient

SIGNUP_PATH = "/api/v1/auth/signup"
APPLICATIONS_PATH = "/api/v1/applications"
ANALYTICS_PATH = "/api/v1/analytics/summary"


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _signup(client: TestClient, email: str) -> dict:
    response = client.post(SIGNUP_PATH, json={"email": email, "password": "password123"})
    assert response.status_code == 201
    return response.json()


def _create_application(client: TestClient, access_token: str, company_name: str = "Owner Co") -> dict:
    response = client.post(
        APPLICATIONS_PATH,
        headers=_auth_headers(access_token),
        json={"company_name": company_name, "role_title": "Engineer"},
    )
    assert response.status_code == 201
    return response.json()


def _create_interview(client: TestClient, access_token: str, application_id: int) -> dict:
    response = client.post(
        f"{APPLICATIONS_PATH}/{application_id}/interviews",
        headers=_auth_headers(access_token),
        json={"round_name": "Phone screen"},
    )
    assert response.status_code == 201
    return response.json()


def test_user_b_cannot_access_or_mutate_user_a_application(client: TestClient) -> None:
    user_a = _signup(client, "usera@example.com")
    user_b = _signup(client, "userb@example.com")
    owned = _create_application(client, user_a["access_token"], "Alpha")
    path = f"{APPLICATIONS_PATH}/{owned['id']}"

    retrieved = client.get(path, headers=_auth_headers(user_a["access_token"]))
    assert retrieved.status_code == 200
    assert retrieved.json()["company_name"] == "Alpha"

    for response in (
        client.get(path, headers=_auth_headers(user_b["access_token"])),
        client.put(
            path,
            headers=_auth_headers(user_b["access_token"]),
            json={"status": "Rejected"},
        ),
        client.delete(path, headers=_auth_headers(user_b["access_token"])),
    ):
        assert response.status_code == 404
        assert response.json()["detail"] == "Application not found"

    still_owned = client.get(path, headers=_auth_headers(user_a["access_token"]))
    assert still_owned.status_code == 200
    assert still_owned.json()["status"] == "Wishlist"


def test_user_b_cannot_access_or_mutate_user_a_interview(client: TestClient) -> None:
    user_a = _signup(client, "usera@example.com")
    user_b = _signup(client, "userb@example.com")
    application = _create_application(client, user_a["access_token"])
    interview = _create_interview(client, user_a["access_token"], application["id"])
    interviews_path = f"{APPLICATIONS_PATH}/{application['id']}/interviews"
    round_path = f"{interviews_path}/{interview['id']}"

    listed = client.get(interviews_path, headers=_auth_headers(user_a["access_token"]))
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == interview["id"]

    for response in (
        client.get(interviews_path, headers=_auth_headers(user_b["access_token"])),
        client.put(
            round_path,
            headers=_auth_headers(user_b["access_token"]),
            json={"outcome": "Failed"},
        ),
        client.delete(round_path, headers=_auth_headers(user_b["access_token"])),
    ):
        assert response.status_code == 404
        assert response.json()["detail"] == "Application not found"

    remaining = client.get(interviews_path, headers=_auth_headers(user_a["access_token"]))
    assert remaining.status_code == 200
    assert remaining.json()[0]["outcome"] == "Pending"


def test_id_manipulation_cannot_reattach_foreign_interview(client: TestClient) -> None:
    user_a = _signup(client, "usera@example.com")
    user_b = _signup(client, "userb@example.com")
    app_a = _create_application(client, user_a["access_token"], "A Co")
    app_b = _create_application(client, user_b["access_token"], "B Co")
    interview_a = _create_interview(client, user_a["access_token"], app_a["id"])

    swapped = client.put(
        f"{APPLICATIONS_PATH}/{app_b['id']}/interviews/{interview_a['id']}",
        headers=_auth_headers(user_b["access_token"]),
        json={"outcome": "Passed"},
    )
    assert swapped.status_code == 404
    assert swapped.json()["detail"] == "Interview round not found"

    original = client.get(
        f"{APPLICATIONS_PATH}/{app_a['id']}/interviews",
        headers=_auth_headers(user_a["access_token"]),
    )
    assert original.json()[0]["outcome"] == "Pending"


def test_list_and_analytics_do_not_leak_other_users_resources(client: TestClient) -> None:
    user_a = _signup(client, "usera@example.com")
    user_b = _signup(client, "userb@example.com")
    _create_application(client, user_a["access_token"], "Secret Co")
    public = _create_application(client, user_b["access_token"], "Public Co")
    _create_interview(client, user_b["access_token"], public["id"])

    listed = client.get(APPLICATIONS_PATH, headers=_auth_headers(user_b["access_token"]))
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["company_name"] == "Public Co"
    assert all(item["user_id"] == user_b["user"]["id"] for item in listed.json()["items"])

    analytics = client.get(ANALYTICS_PATH, headers=_auth_headers(user_b["access_token"]))
    assert analytics.status_code == 200
    assert analytics.json()["total_applications"] == 1
    assert analytics.json()["interview_count"] == 1
