from fastapi.testclient import TestClient

SIGNUP_PATH = "/api/v1/auth/signup"
APPLICATIONS_PATH = "/api/v1/applications"


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


def _create_application(
    client: TestClient,
    access_token: str,
    *,
    company_name: str = "Acme",
    role_title: str = "Software Engineer",
    status: str = "Wishlist",
    applied_date: str | None = None,
    deadline: str | None = None,
    notes: str | None = None,
    job_description: str | None = None,
    resume_version: str | None = None,
):
    payload: dict = {
        "company_name": company_name,
        "role_title": role_title,
        "status": status,
    }
    if applied_date is not None:
        payload["applied_date"] = applied_date
    if deadline is not None:
        payload["deadline"] = deadline
    if notes is not None:
        payload["notes"] = notes
    if job_description is not None:
        payload["job_description"] = job_description
    if resume_version is not None:
        payload["resume_version"] = resume_version
    return client.post(
        APPLICATIONS_PATH,
        headers=_auth_headers(access_token),
        json=payload,
    )


def test_authenticated_user_can_create_application(client: TestClient) -> None:
    tokens = _signup(client)
    response = _create_application(
        client,
        tokens["access_token"],
        notes="Follow up next week",
        job_description="Build APIs",
        resume_version="v2",
        applied_date="2026-03-01",
        deadline="2026-03-15",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["company_name"] == "Acme"
    assert body["role_title"] == "Software Engineer"
    assert body["status"] == "Wishlist"
    assert body["user_id"] == tokens["user"]["id"]
    assert body["notes"] == "Follow up next week"
    assert body["job_description"] == "Build APIs"
    assert body["resume_version"] == "v2"
    assert body["applied_date"] == "2026-03-01"
    assert body["deadline"] == "2026-03-15"
    assert body["id"]
    assert body["created_at"]
    assert body["updated_at"]


def test_unauthenticated_user_cannot_access_application_endpoints(client: TestClient) -> None:
    created = client.post(
        APPLICATIONS_PATH,
        json={"company_name": "Acme", "role_title": "Engineer"},
    )
    listed = client.get(APPLICATIONS_PATH)
    retrieved = client.get(f"{APPLICATIONS_PATH}/1")
    updated = client.put(
        f"{APPLICATIONS_PATH}/1",
        json={"company_name": "Other"},
    )
    deleted = client.delete(f"{APPLICATIONS_PATH}/1")

    for response in (created, listed, retrieved, updated, deleted):
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"


def test_authenticated_user_can_list_their_applications(client: TestClient) -> None:
    tokens = _signup(client)
    _create_application(client, tokens["access_token"], company_name="Acme")
    _create_application(client, tokens["access_token"], company_name="Globex")

    response = client.get(APPLICATIONS_PATH, headers=_auth_headers(tokens["access_token"]))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert {item["company_name"] for item in body["items"]} == {"Acme", "Globex"}
    assert all(item["user_id"] == tokens["user"]["id"] for item in body["items"])


def test_list_does_not_include_other_users_applications(client: TestClient) -> None:
    owner = _signup(client, email="owner@example.com")
    other = _signup(client, email="other@example.com")
    _create_application(client, owner["access_token"], company_name="Owner Co")
    _create_application(client, other["access_token"], company_name="Other Co")

    response = client.get(APPLICATIONS_PATH, headers=_auth_headers(owner["access_token"]))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["company_name"] == "Owner Co"


def test_authenticated_user_can_retrieve_own_application(client: TestClient) -> None:
    tokens = _signup(client)
    created = _create_application(client, tokens["access_token"]).json()

    response = client.get(
        f"{APPLICATIONS_PATH}/{created['id']}",
        headers=_auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["company_name"] == "Acme"


def test_authenticated_user_can_update_own_application(client: TestClient) -> None:
    tokens = _signup(client)
    created = _create_application(client, tokens["access_token"]).json()

    response = client.put(
        f"{APPLICATIONS_PATH}/{created['id']}",
        headers=_auth_headers(tokens["access_token"]),
        json={"status": "Applied", "notes": "Submitted"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "Applied"
    assert body["notes"] == "Submitted"
    assert body["company_name"] == "Acme"
    assert body["role_title"] == "Software Engineer"


def test_authenticated_user_can_delete_own_application(client: TestClient) -> None:
    tokens = _signup(client)
    created = _create_application(client, tokens["access_token"]).json()

    response = client.delete(
        f"{APPLICATIONS_PATH}/{created['id']}",
        headers=_auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 204
    assert response.content == b""

    missing = client.get(
        f"{APPLICATIONS_PATH}/{created['id']}",
        headers=_auth_headers(tokens["access_token"]),
    )
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Application not found"


def test_user_cannot_retrieve_another_users_application(client: TestClient) -> None:
    owner = _signup(client, email="owner@example.com")
    other = _signup(client, email="other@example.com")
    created = _create_application(client, owner["access_token"]).json()

    response = client.get(
        f"{APPLICATIONS_PATH}/{created['id']}",
        headers=_auth_headers(other["access_token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"


def test_user_cannot_update_another_users_application(client: TestClient) -> None:
    owner = _signup(client, email="owner@example.com")
    other = _signup(client, email="other@example.com")
    created = _create_application(client, owner["access_token"]).json()

    response = client.put(
        f"{APPLICATIONS_PATH}/{created['id']}",
        headers=_auth_headers(other["access_token"]),
        json={"status": "Rejected"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"

    original = client.get(
        f"{APPLICATIONS_PATH}/{created['id']}",
        headers=_auth_headers(owner["access_token"]),
    )
    assert original.status_code == 200
    assert original.json()["status"] == "Wishlist"


def test_user_cannot_delete_another_users_application(client: TestClient) -> None:
    owner = _signup(client, email="owner@example.com")
    other = _signup(client, email="other@example.com")
    created = _create_application(client, owner["access_token"]).json()

    response = client.delete(
        f"{APPLICATIONS_PATH}/{created['id']}",
        headers=_auth_headers(other["access_token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"

    still_there = client.get(
        f"{APPLICATIONS_PATH}/{created['id']}",
        headers=_auth_headers(owner["access_token"]),
    )
    assert still_there.status_code == 200


def test_missing_application_returns_404(client: TestClient) -> None:
    tokens = _signup(client)

    response = client.get(
        f"{APPLICATIONS_PATH}/9999",
        headers=_auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"


def test_pagination(client: TestClient) -> None:
    tokens = _signup(client)
    for index in range(5):
        _create_application(
            client,
            tokens["access_token"],
            company_name=f"Company {index}",
            role_title=f"Role {index}",
        )

    page_one = client.get(
        APPLICATIONS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        params={"page": 1, "page_size": 2, "sort": "company_name", "order": "asc"},
    )
    page_two = client.get(
        APPLICATIONS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        params={"page": 2, "page_size": 2, "sort": "company_name", "order": "asc"},
    )
    page_three = client.get(
        APPLICATIONS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        params={"page": 3, "page_size": 2, "sort": "company_name", "order": "asc"},
    )

    assert page_one.status_code == 200
    assert page_one.json()["total"] == 5
    assert page_one.json()["page"] == 1
    assert page_one.json()["page_size"] == 2
    assert [item["company_name"] for item in page_one.json()["items"]] == [
        "Company 0",
        "Company 1",
    ]
    assert [item["company_name"] for item in page_two.json()["items"]] == [
        "Company 2",
        "Company 3",
    ]
    assert [item["company_name"] for item in page_three.json()["items"]] == ["Company 4"]


def test_sorting(client: TestClient) -> None:
    tokens = _signup(client)
    _create_application(client, tokens["access_token"], company_name="Zebra")
    _create_application(client, tokens["access_token"], company_name="Acme")
    _create_application(client, tokens["access_token"], company_name="Monarch")

    ascending = client.get(
        APPLICATIONS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        params={"sort": "company_name", "order": "asc"},
    )
    descending = client.get(
        APPLICATIONS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        params={"sort": "company_name", "order": "desc"},
    )

    assert [item["company_name"] for item in ascending.json()["items"]] == [
        "Acme",
        "Monarch",
        "Zebra",
    ]
    assert [item["company_name"] for item in descending.json()["items"]] == [
        "Zebra",
        "Monarch",
        "Acme",
    ]


def test_status_filtering(client: TestClient) -> None:
    tokens = _signup(client)
    _create_application(client, tokens["access_token"], company_name="A", status="Wishlist")
    _create_application(client, tokens["access_token"], company_name="B", status="Applied")
    _create_application(client, tokens["access_token"], company_name="C", status="Applied")

    response = client.get(
        APPLICATIONS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        params={"status": "Applied"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert {item["company_name"] for item in body["items"]} == {"B", "C"}
    assert all(item["status"] == "Applied" for item in body["items"])


def test_company_filtering(client: TestClient) -> None:
    tokens = _signup(client)
    _create_application(client, tokens["access_token"], company_name="Acme")
    _create_application(client, tokens["access_token"], company_name="Globex")
    _create_application(client, tokens["access_token"], company_name="Acme Labs")

    response = client.get(
        APPLICATIONS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        params={"company": "acme"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["company_name"] == "Acme"


def test_deadline_before_filtering(client: TestClient) -> None:
    tokens = _signup(client)
    _create_application(client, tokens["access_token"], company_name="Early", deadline="2026-01-10")
    _create_application(client, tokens["access_token"], company_name="Late", deadline="2026-03-10")
    _create_application(client, tokens["access_token"], company_name="None")

    response = client.get(
        APPLICATIONS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        params={"deadline_before": "2026-02-01"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["company_name"] == "Early"


def test_deadline_after_filtering(client: TestClient) -> None:
    tokens = _signup(client)
    _create_application(client, tokens["access_token"], company_name="Early", deadline="2026-01-10")
    _create_application(client, tokens["access_token"], company_name="Late", deadline="2026-03-10")
    _create_application(client, tokens["access_token"], company_name="None")

    response = client.get(
        APPLICATIONS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        params={"deadline_after": "2026-02-01"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["company_name"] == "Late"


def test_search_matches_company_or_role(client: TestClient) -> None:
    tokens = _signup(client)
    _create_application(
        client,
        tokens["access_token"],
        company_name="Northern Lights",
        role_title="Backend Engineer",
    )
    _create_application(
        client,
        tokens["access_token"],
        company_name="Globex",
        role_title="Data Analyst",
    )
    _create_application(
        client,
        tokens["access_token"],
        company_name="Initech",
        role_title="Frontend Engineer",
    )

    by_company = client.get(
        APPLICATIONS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        params={"search": "northern"},
    )
    by_role = client.get(
        APPLICATIONS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        params={"search": "engineer"},
    )

    assert by_company.json()["total"] == 1
    assert by_company.json()["items"][0]["company_name"] == "Northern Lights"
    assert by_role.json()["total"] == 2
    assert {item["company_name"] for item in by_role.json()["items"]} == {
        "Northern Lights",
        "Initech",
    }


def test_search_escapes_like_wildcards(client: TestClient) -> None:
    tokens = _signup(client)
    _create_application(client, tokens["access_token"], company_name="Acme")
    _create_application(client, tokens["access_token"], company_name="Globex")

    response = client.get(
        APPLICATIONS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        params={"search": "%"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_create_requires_company_and_role(client: TestClient) -> None:
    tokens = _signup(client)
    response = client.post(
        APPLICATIONS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        json={"company_name": "   ", "role_title": ""},
    )

    assert response.status_code == 422


def test_create_rejects_excessively_long_company_name(client: TestClient) -> None:
    tokens = _signup(client)
    response = _create_application(
        client,
        tokens["access_token"],
        company_name="A" * 256,
    )

    assert response.status_code == 422


def test_create_rejects_invalid_date(client: TestClient) -> None:
    tokens = _signup(client)
    response = client.post(
        APPLICATIONS_PATH,
        headers=_auth_headers(tokens["access_token"]),
        json={
            "company_name": "Acme",
            "role_title": "Engineer",
            "applied_date": "not-a-date",
        },
    )

    assert response.status_code == 422


def test_retrieve_rejects_non_integer_id(client: TestClient) -> None:
    tokens = _signup(client)
    response = client.get(
        f"{APPLICATIONS_PATH}/not-an-id",
        headers=_auth_headers(tokens["access_token"]),
    )

    assert response.status_code == 422


def test_create_rejects_invalid_status(client: TestClient) -> None:
    tokens = _signup(client)
    response = _create_application(
        client,
        tokens["access_token"],
        status="Interviewed",
    )

    assert response.status_code == 422


def test_update_rejects_empty_payload(client: TestClient) -> None:
    tokens = _signup(client)
    created = _create_application(client, tokens["access_token"]).json()

    response = client.put(
        f"{APPLICATIONS_PATH}/{created['id']}",
        headers=_auth_headers(tokens["access_token"]),
        json={},
    )

    assert response.status_code == 422


def test_list_rejects_invalid_pagination_and_sort(client: TestClient) -> None:
    tokens = _signup(client)
    headers = _auth_headers(tokens["access_token"])

    page_zero = client.get(APPLICATIONS_PATH, headers=headers, params={"page": 0})
    oversized = client.get(APPLICATIONS_PATH, headers=headers, params={"page_size": 101})
    bad_sort = client.get(APPLICATIONS_PATH, headers=headers, params={"sort": "salary"})
    bad_status = client.get(APPLICATIONS_PATH, headers=headers, params={"status": "Maybe"})

    assert page_zero.status_code == 422
    assert oversized.status_code == 422
    assert bad_sort.status_code == 422
    assert bad_status.status_code == 422
