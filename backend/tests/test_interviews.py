from fastapi.testclient import TestClient

SIGNUP_PATH = "/api/v1/auth/signup"
APPLICATIONS_PATH = "/api/v1/applications"

INTERVIEW_PUBLIC_FIELDS = {
    "id",
    "application_id",
    "round_name",
    "scheduled_at",
    "notes",
    "outcome",
}


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _signup(
    client: TestClient,
    email: str = "user@example.com",
    password: str = "password123",
) -> dict:
    response = client.post(SIGNUP_PATH, json={"email": email, "password": password})
    assert response.status_code == 201
    return response.json()


def _create_application(client: TestClient, access_token: str) -> dict:
    response = client.post(
        APPLICATIONS_PATH,
        headers=_auth_headers(access_token),
        json={"company_name": "Acme", "role_title": "Software Engineer"},
    )
    assert response.status_code == 201
    return response.json()


def _interviews_path(application_id: int) -> str:
    return f"{APPLICATIONS_PATH}/{application_id}/interviews"


def _create_interview(
    client: TestClient,
    access_token: str,
    application_id: int,
    *,
    round_name: str = "Phone screen",
    scheduled_at: str | None = "2026-04-01T15:00:00+00:00",
    notes: str | None = None,
    outcome: str | None = None,
):
    payload: dict = {"round_name": round_name}
    if scheduled_at is not None:
        payload["scheduled_at"] = scheduled_at
    if notes is not None:
        payload["notes"] = notes
    if outcome is not None:
        payload["outcome"] = outcome
    return client.post(
        _interviews_path(application_id),
        headers=_auth_headers(access_token),
        json=payload,
    )


def test_authenticated_user_can_list_interview_rounds(client: TestClient) -> None:
    tokens = _signup(client)
    application = _create_application(client, tokens["access_token"])
    first = _create_interview(
        client,
        tokens["access_token"],
        application["id"],
        round_name="Onsite",
        scheduled_at="2026-04-10T10:00:00+00:00",
    )
    second = _create_interview(
        client,
        tokens["access_token"],
        application["id"],
        round_name="Phone screen",
        scheduled_at="2026-04-01T15:00:00+00:00",
    )
    unscheduled = _create_interview(
        client,
        tokens["access_token"],
        application["id"],
        round_name="Offer call",
        scheduled_at=None,
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert unscheduled.status_code == 201

    response = client.get(
        _interviews_path(application["id"]),
        headers=_auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["round_name"] for item in body] == [
        "Phone screen",
        "Onsite",
        "Offer call",
    ]
    assert all(item["application_id"] == application["id"] for item in body)


def test_authenticated_user_can_create_interview_round(client: TestClient) -> None:
    tokens = _signup(client)
    application = _create_application(client, tokens["access_token"])

    response = _create_interview(
        client,
        tokens["access_token"],
        application["id"],
        notes="Ask about team structure",
        outcome="Pending",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["round_name"] == "Phone screen"
    assert body["application_id"] == application["id"]
    assert body["scheduled_at"] == "2026-04-01T15:00:00Z"
    assert body["notes"] == "Ask about team structure"
    assert body["outcome"] == "Pending"
    assert body["id"]


def test_create_defaults_outcome_to_pending(client: TestClient) -> None:
    tokens = _signup(client)
    application = _create_application(client, tokens["access_token"])

    response = _create_interview(
        client,
        tokens["access_token"],
        application["id"],
        scheduled_at=None,
    )

    assert response.status_code == 201
    assert response.json()["outcome"] == "Pending"
    assert response.json()["scheduled_at"] is None


def test_authenticated_user_can_update_own_interview_round(client: TestClient) -> None:
    tokens = _signup(client)
    application = _create_application(client, tokens["access_token"])
    created = _create_interview(
        client,
        tokens["access_token"],
        application["id"],
    ).json()

    response = client.put(
        f"{_interviews_path(application['id'])}/{created['id']}",
        headers=_auth_headers(tokens["access_token"]),
        json={"outcome": "Passed", "notes": "Strong system design"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] == "Passed"
    assert body["notes"] == "Strong system design"
    assert body["round_name"] == "Phone screen"
    assert body["scheduled_at"] == "2026-04-01T15:00:00Z"


def test_authenticated_user_can_delete_own_interview_round(client: TestClient) -> None:
    tokens = _signup(client)
    application = _create_application(client, tokens["access_token"])
    created = _create_interview(
        client,
        tokens["access_token"],
        application["id"],
    ).json()

    response = client.delete(
        f"{_interviews_path(application['id'])}/{created['id']}",
        headers=_auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 204
    assert response.content == b""

    listed = client.get(
        _interviews_path(application["id"]),
        headers=_auth_headers(tokens["access_token"]),
    )
    assert listed.status_code == 200
    assert listed.json() == []


def test_unauthenticated_requests_are_rejected(client: TestClient) -> None:
    listed = client.get(f"{APPLICATIONS_PATH}/1/interviews")
    created = client.post(
        f"{APPLICATIONS_PATH}/1/interviews",
        json={"round_name": "Phone screen"},
    )
    updated = client.put(
        f"{APPLICATIONS_PATH}/1/interviews/1",
        json={"outcome": "Passed"},
    )
    deleted = client.delete(f"{APPLICATIONS_PATH}/1/interviews/1")

    for response in (listed, created, updated, deleted):
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"


def test_user_cannot_list_another_users_application_interviews(client: TestClient) -> None:
    owner = _signup(client, email="owner@example.com")
    other = _signup(client, email="other@example.com")
    application = _create_application(client, owner["access_token"])
    _create_interview(client, owner["access_token"], application["id"])

    response = client.get(
        _interviews_path(application["id"]),
        headers=_auth_headers(other["access_token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"


def test_user_cannot_create_interview_under_another_users_application(
    client: TestClient,
) -> None:
    owner = _signup(client, email="owner@example.com")
    other = _signup(client, email="other@example.com")
    application = _create_application(client, owner["access_token"])

    response = _create_interview(client, other["access_token"], application["id"])

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"

    listed = client.get(
        _interviews_path(application["id"]),
        headers=_auth_headers(owner["access_token"]),
    )
    assert listed.status_code == 200
    assert listed.json() == []


def test_user_cannot_update_another_users_interview_round(client: TestClient) -> None:
    owner = _signup(client, email="owner@example.com")
    other = _signup(client, email="other@example.com")
    application = _create_application(client, owner["access_token"])
    created = _create_interview(client, owner["access_token"], application["id"]).json()

    response = client.put(
        f"{_interviews_path(application['id'])}/{created['id']}",
        headers=_auth_headers(other["access_token"]),
        json={"outcome": "Failed"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"

    original = client.get(
        _interviews_path(application["id"]),
        headers=_auth_headers(owner["access_token"]),
    )
    assert original.status_code == 200
    assert original.json()[0]["outcome"] == "Pending"


def test_user_cannot_delete_another_users_interview_round(client: TestClient) -> None:
    owner = _signup(client, email="owner@example.com")
    other = _signup(client, email="other@example.com")
    application = _create_application(client, owner["access_token"])
    created = _create_interview(client, owner["access_token"], application["id"]).json()

    response = client.delete(
        f"{_interviews_path(application['id'])}/{created['id']}",
        headers=_auth_headers(other["access_token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"

    still_there = client.get(
        _interviews_path(application["id"]),
        headers=_auth_headers(owner["access_token"]),
    )
    assert still_there.status_code == 200
    assert len(still_there.json()) == 1
    assert still_there.json()[0]["id"] == created["id"]


def test_user_cannot_update_interview_using_own_application_and_foreign_round(
    client: TestClient,
) -> None:
    owner = _signup(client, email="owner@example.com")
    other = _signup(client, email="other@example.com")
    owner_app = _create_application(client, owner["access_token"])
    other_app = _create_application(client, other["access_token"])
    foreign = _create_interview(client, other["access_token"], other_app["id"]).json()

    response = client.put(
        f"{_interviews_path(owner_app['id'])}/{foreign['id']}",
        headers=_auth_headers(owner["access_token"]),
        json={"outcome": "Passed"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Interview round not found"


def test_nonexistent_application_returns_404(client: TestClient) -> None:
    tokens = _signup(client)

    listed = client.get(
        _interviews_path(9999),
        headers=_auth_headers(tokens["access_token"]),
    )
    created = _create_interview(client, tokens["access_token"], 9999)
    updated = client.put(
        f"{_interviews_path(9999)}/1",
        headers=_auth_headers(tokens["access_token"]),
        json={"outcome": "Passed"},
    )
    deleted = client.delete(
        f"{_interviews_path(9999)}/1",
        headers=_auth_headers(tokens["access_token"]),
    )

    for response in (listed, created, updated, deleted):
        assert response.status_code == 404
        assert response.json()["detail"] == "Application not found"


def test_nonexistent_interview_round_returns_404(client: TestClient) -> None:
    tokens = _signup(client)
    application = _create_application(client, tokens["access_token"])

    updated = client.put(
        f"{_interviews_path(application['id'])}/9999",
        headers=_auth_headers(tokens["access_token"]),
        json={"outcome": "Passed"},
    )
    deleted = client.delete(
        f"{_interviews_path(application['id'])}/9999",
        headers=_auth_headers(tokens["access_token"]),
    )

    assert updated.status_code == 404
    assert updated.json()["detail"] == "Interview round not found"
    assert deleted.status_code == 404
    assert deleted.json()["detail"] == "Interview round not found"


def test_round_name_validation(client: TestClient) -> None:
    tokens = _signup(client)
    application = _create_application(client, tokens["access_token"])
    created = _create_interview(client, tokens["access_token"], application["id"]).json()

    blank = _create_interview(
        client,
        tokens["access_token"],
        application["id"],
        round_name="   ",
    )
    missing = client.post(
        _interviews_path(application["id"]),
        headers=_auth_headers(tokens["access_token"]),
        json={},
    )
    too_long = _create_interview(
        client,
        tokens["access_token"],
        application["id"],
        round_name="x" * 256,
    )
    update_blank = client.put(
        f"{_interviews_path(application['id'])}/{created['id']}",
        headers=_auth_headers(tokens["access_token"]),
        json={"round_name": "  "},
    )

    assert blank.status_code == 422
    assert missing.status_code == 422
    assert too_long.status_code == 422
    assert update_blank.status_code == 422


def test_scheduled_time_validation(client: TestClient) -> None:
    tokens = _signup(client)
    application = _create_application(client, tokens["access_token"])
    created = _create_interview(client, tokens["access_token"], application["id"]).json()

    invalid = _create_interview(
        client,
        tokens["access_token"],
        application["id"],
        scheduled_at="not-a-datetime",
    )
    naive = _create_interview(
        client,
        tokens["access_token"],
        application["id"],
        scheduled_at="2026-04-01T15:00:00",
    )
    update_naive = client.put(
        f"{_interviews_path(application['id'])}/{created['id']}",
        headers=_auth_headers(tokens["access_token"]),
        json={"scheduled_at": "2026-04-01T15:00:00"},
    )

    assert invalid.status_code == 422
    assert naive.status_code == 422
    assert update_naive.status_code == 422


def test_outcome_validation(client: TestClient) -> None:
    tokens = _signup(client)
    application = _create_application(client, tokens["access_token"])
    created = _create_interview(client, tokens["access_token"], application["id"]).json()

    invalid_create = _create_interview(
        client,
        tokens["access_token"],
        application["id"],
        outcome="Maybe",
    )
    invalid_update = client.put(
        f"{_interviews_path(application['id'])}/{created['id']}",
        headers=_auth_headers(tokens["access_token"]),
        json={"outcome": "Ghosted"},
    )

    assert invalid_create.status_code == 422
    assert invalid_update.status_code == 422


def test_update_rejects_empty_payload(client: TestClient) -> None:
    tokens = _signup(client)
    application = _create_application(client, tokens["access_token"])
    created = _create_interview(client, tokens["access_token"], application["id"]).json()

    response = client.put(
        f"{_interviews_path(application['id'])}/{created['id']}",
        headers=_auth_headers(tokens["access_token"]),
        json={},
    )

    assert response.status_code == 422


def test_interview_response_does_not_expose_unintended_fields(client: TestClient) -> None:
    tokens = _signup(client)
    application = _create_application(client, tokens["access_token"])
    created = _create_interview(client, tokens["access_token"], application["id"]).json()

    listed = client.get(
        _interviews_path(application["id"]),
        headers=_auth_headers(tokens["access_token"]),
    )
    updated = client.put(
        f"{_interviews_path(application['id'])}/{created['id']}",
        headers=_auth_headers(tokens["access_token"]),
        json={"notes": "Follow up"},
    )

    assert set(created.keys()) == INTERVIEW_PUBLIC_FIELDS
    assert set(listed.json()[0].keys()) == INTERVIEW_PUBLIC_FIELDS
    assert set(updated.json().keys()) == INTERVIEW_PUBLIC_FIELDS
    assert "user_id" not in created
    assert "hashed_password" not in created
    assert "application" not in created
