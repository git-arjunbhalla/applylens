from datetime import timedelta

from fastapi.testclient import TestClient

from app.models.enums import ApplicationStatus
from app.services.analytics import upcoming_deadline_window, utc_today

SIGNUP_PATH = "/api/v1/auth/signup"
APPLICATIONS_PATH = "/api/v1/applications"
ANALYTICS_PATH = "/api/v1/analytics/summary"

ANALYTICS_FIELDS = {
    "total_applications",
    "counts_by_status",
    "upcoming_deadlines",
    "interview_count",
    "offers",
    "rejections",
    "response_rate",
    "average_time_to_response_days",
}

STATUS_COUNT_FIELDS = {status.value for status in ApplicationStatus}


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
    response = client.post(
        APPLICATIONS_PATH,
        headers=_auth_headers(access_token),
        json=payload,
    )
    assert response.status_code == 201
    return response.json()


def _create_interview(
    client: TestClient,
    access_token: str,
    application_id: int,
    *,
    round_name: str = "Phone screen",
    outcome: str = "Pending",
):
    response = client.post(
        f"{APPLICATIONS_PATH}/{application_id}/interviews",
        headers=_auth_headers(access_token),
        json={
            "round_name": round_name,
            "scheduled_at": "2026-04-01T15:00:00+00:00",
            "outcome": outcome,
        },
    )
    assert response.status_code == 201
    return response.json()


def _get_summary(client: TestClient, access_token: str):
    return client.get(ANALYTICS_PATH, headers=_auth_headers(access_token))


def _iso(day) -> str:
    return day.isoformat()


def test_authenticated_user_can_access_analytics(client: TestClient) -> None:
    tokens = _signup(client)
    response = _get_summary(client, tokens["access_token"])

    assert response.status_code == 200
    body = response.json()
    assert body["total_applications"] == 0
    assert body["interview_count"] == 0


def test_unauthenticated_user_cannot_access_analytics(client: TestClient) -> None:
    response = client.get(ANALYTICS_PATH)

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_invalid_token_cannot_access_analytics(client: TestClient) -> None:
    response = client.get(
        ANALYTICS_PATH,
        headers=_auth_headers("not-a-token"),
    )

    assert response.status_code == 401


def test_analytics_include_only_authenticated_user_data(client: TestClient) -> None:
    alice = _signup(client, email="alice@example.com")
    bob = _signup(client, email="bob@example.com")

    alice_offer = _create_application(
        client,
        alice["access_token"],
        company_name="Alice Co",
        status="Offer",
        deadline=_iso(utc_today()),
    )
    _create_interview(client, alice["access_token"], alice_offer["id"])

    bob_rejected = _create_application(
        client,
        bob["access_token"],
        company_name="Bob Co",
        status="Rejected",
        deadline=_iso(utc_today()),
    )
    _create_application(
        client,
        bob["access_token"],
        company_name="Bob Wishlist",
        status="Wishlist",
    )
    _create_interview(client, bob["access_token"], bob_rejected["id"], round_name="Onsite")
    _create_interview(client, bob["access_token"], bob_rejected["id"], round_name="Loop")

    alice_summary = _get_summary(client, alice["access_token"]).json()
    bob_summary = _get_summary(client, bob["access_token"]).json()

    assert alice_summary["total_applications"] == 1
    assert alice_summary["offers"] == 1
    assert alice_summary["rejections"] == 0
    assert alice_summary["interview_count"] == 1
    assert alice_summary["upcoming_deadlines"] == 1
    assert alice_summary["counts_by_status"]["Offer"] == 1
    assert alice_summary["counts_by_status"]["Rejected"] == 0

    assert bob_summary["total_applications"] == 2
    assert bob_summary["offers"] == 0
    assert bob_summary["rejections"] == 1
    assert bob_summary["interview_count"] == 2
    assert bob_summary["upcoming_deadlines"] == 1
    assert bob_summary["counts_by_status"]["Rejected"] == 1
    assert bob_summary["counts_by_status"]["Wishlist"] == 1
    assert bob_summary["counts_by_status"]["Offer"] == 0


def test_total_application_count(client: TestClient) -> None:
    tokens = _signup(client)
    _create_application(client, tokens["access_token"], company_name="One")
    _create_application(client, tokens["access_token"], company_name="Two")
    _create_application(client, tokens["access_token"], company_name="Three")

    body = _get_summary(client, tokens["access_token"]).json()
    assert body["total_applications"] == 3


def test_counts_by_each_application_status(client: TestClient) -> None:
    tokens = _signup(client)
    statuses = [
        "Wishlist",
        "Applied",
        "Applied",
        "OA",
        "Interviewing",
        "Offer",
        "Rejected",
        "Rejected",
    ]
    for index, status in enumerate(statuses):
        _create_application(
            client,
            tokens["access_token"],
            company_name=f"Company {index}",
            status=status,
        )

    body = _get_summary(client, tokens["access_token"]).json()
    counts = body["counts_by_status"]
    assert counts["Wishlist"] == 1
    assert counts["Applied"] == 2
    assert counts["OA"] == 1
    assert counts["Interviewing"] == 1
    assert counts["Offer"] == 1
    assert counts["Rejected"] == 2
    assert body["total_applications"] == 8
    assert set(counts) == STATUS_COUNT_FIELDS


def test_deadlines_within_next_seven_days_are_included(client: TestClient) -> None:
    tokens = _signup(client)
    start, end = upcoming_deadline_window(utc_today())
    mid = start + timedelta(days=3)

    _create_application(
        client,
        tokens["access_token"],
        company_name="Due today",
        deadline=_iso(start),
    )
    _create_application(
        client,
        tokens["access_token"],
        company_name="Due mid window",
        deadline=_iso(mid),
    )
    _create_application(
        client,
        tokens["access_token"],
        company_name="Due on day 7",
        deadline=_iso(end),
    )

    body = _get_summary(client, tokens["access_token"]).json()
    assert body["upcoming_deadlines"] == 3


def test_deadlines_outside_window_are_excluded(client: TestClient) -> None:
    tokens = _signup(client)
    start, end = upcoming_deadline_window(utc_today())

    _create_application(
        client,
        tokens["access_token"],
        company_name="Yesterday",
        deadline=_iso(start - timedelta(days=1)),
    )
    _create_application(
        client,
        tokens["access_token"],
        company_name="Day 8",
        deadline=_iso(end + timedelta(days=1)),
    )
    _create_application(
        client,
        tokens["access_token"],
        company_name="Far future",
        deadline=_iso(end + timedelta(days=30)),
    )

    body = _get_summary(client, tokens["access_token"]).json()
    assert body["upcoming_deadlines"] == 0
    assert body["total_applications"] == 3


def test_null_deadlines_are_excluded_from_upcoming_count(client: TestClient) -> None:
    tokens = _signup(client)
    _create_application(client, tokens["access_token"], company_name="No deadline")
    _create_application(
        client,
        tokens["access_token"],
        company_name="Has deadline",
        deadline=_iso(utc_today()),
    )

    body = _get_summary(client, tokens["access_token"]).json()
    assert body["total_applications"] == 2
    assert body["upcoming_deadlines"] == 1


def test_interview_count(client: TestClient) -> None:
    tokens = _signup(client)
    first = _create_application(client, tokens["access_token"], company_name="First")
    second = _create_application(client, tokens["access_token"], company_name="Second")
    _create_interview(client, tokens["access_token"], first["id"], round_name="Screen")
    _create_interview(client, tokens["access_token"], first["id"], round_name="Onsite")
    _create_interview(client, tokens["access_token"], second["id"], round_name="Recruiter")

    body = _get_summary(client, tokens["access_token"]).json()
    assert body["interview_count"] == 3
    assert body["total_applications"] == 2


def test_offers_and_rejections_use_application_status(client: TestClient) -> None:
    tokens = _signup(client)
    offer = _create_application(
        client,
        tokens["access_token"],
        company_name="Offer Co",
        status="Offer",
    )
    rejected = _create_application(
        client,
        tokens["access_token"],
        company_name="Rejected Co",
        status="Rejected",
    )
    interviewing = _create_application(
        client,
        tokens["access_token"],
        company_name="Interview Co",
        status="Interviewing",
    )
    _create_interview(
        client,
        tokens["access_token"],
        offer["id"],
        outcome="Passed",
    )
    _create_interview(
        client,
        tokens["access_token"],
        rejected["id"],
        outcome="Failed",
    )
    _create_interview(
        client,
        tokens["access_token"],
        interviewing["id"],
        outcome="Failed",
    )

    body = _get_summary(client, tokens["access_token"]).json()
    assert body["offers"] == 1
    assert body["rejections"] == 1
    assert body["counts_by_status"]["Interviewing"] == 1


def test_response_rate_calculation(client: TestClient) -> None:
    tokens = _signup(client)
    _create_application(client, tokens["access_token"], company_name="Wish", status="Wishlist")
    _create_application(client, tokens["access_token"], company_name="Silent", status="Applied")
    _create_application(client, tokens["access_token"], company_name="OA Co", status="OA")
    _create_application(client, tokens["access_token"], company_name="Talk", status="Interviewing")
    _create_application(client, tokens["access_token"], company_name="Win", status="Offer")
    _create_application(client, tokens["access_token"], company_name="Loss", status="Rejected")

    body = _get_summary(client, tokens["access_token"]).json()
    # submitted = 5 (excludes Wishlist); responded = 4 (excludes Applied)
    assert body["response_rate"] == 0.8


def test_zero_application_edge_cases(client: TestClient) -> None:
    tokens = _signup(client)
    body = _get_summary(client, tokens["access_token"]).json()

    assert body["total_applications"] == 0
    assert body["upcoming_deadlines"] == 0
    assert body["interview_count"] == 0
    assert body["offers"] == 0
    assert body["rejections"] == 0
    assert body["response_rate"] == 0.0
    assert body["average_time_to_response_days"] is None
    assert body["counts_by_status"] == {
        "Wishlist": 0,
        "Applied": 0,
        "OA": 0,
        "Interviewing": 0,
        "Offer": 0,
        "Rejected": 0,
    }


def test_zero_response_rate_when_only_wishlist_or_applied(client: TestClient) -> None:
    tokens = _signup(client)
    _create_application(client, tokens["access_token"], company_name="Wish", status="Wishlist")
    _create_application(client, tokens["access_token"], company_name="Silent", status="Applied")

    body = _get_summary(client, tokens["access_token"]).json()
    assert body["response_rate"] == 0.0
    assert body["total_applications"] == 2


def test_optional_applied_date_does_not_invent_time_to_response(
    client: TestClient,
) -> None:
    tokens = _signup(client)
    _create_application(
        client,
        tokens["access_token"],
        company_name="No applied date",
        status="Offer",
    )
    _create_application(
        client,
        tokens["access_token"],
        company_name="Has applied date",
        status="Rejected",
        applied_date="2026-01-15",
    )

    body = _get_summary(client, tokens["access_token"]).json()
    assert body["average_time_to_response_days"] is None
    assert body["offers"] == 1
    assert body["rejections"] == 1


def test_average_time_to_response_is_null_without_response_timestamp(
    client: TestClient,
) -> None:
    tokens = _signup(client)
    _create_application(
        client,
        tokens["access_token"],
        status="Offer",
        applied_date="2026-01-01",
    )

    body = _get_summary(client, tokens["access_token"]).json()
    assert "average_time_to_response_days" in body
    assert body["average_time_to_response_days"] is None


def test_joins_do_not_duplicate_application_or_interview_counts(
    client: TestClient,
) -> None:
    tokens = _signup(client)
    heavy = _create_application(
        client,
        tokens["access_token"],
        company_name="Many rounds",
        status="Interviewing",
        deadline=_iso(utc_today()),
    )
    _create_application(
        client,
        tokens["access_token"],
        company_name="No rounds",
        status="Applied",
        deadline=_iso(utc_today()),
    )
    for name in ("Screen", "Tech", "Onsite", "Loop"):
        _create_interview(client, tokens["access_token"], heavy["id"], round_name=name)

    body = _get_summary(client, tokens["access_token"]).json()
    assert body["total_applications"] == 2
    assert body["upcoming_deadlines"] == 2
    assert body["interview_count"] == 4
    assert body["counts_by_status"]["Interviewing"] == 1
    assert body["counts_by_status"]["Applied"] == 1


def test_response_schema_contains_only_intended_fields(client: TestClient) -> None:
    tokens = _signup(client)
    _create_application(client, tokens["access_token"])
    body = _get_summary(client, tokens["access_token"]).json()

    assert set(body) == ANALYTICS_FIELDS
    assert set(body["counts_by_status"]) == STATUS_COUNT_FIELDS
    assert "user_id" not in body
    assert "hashed_password" not in body
    assert "applications" not in body
    assert "interview_rounds" not in body
