from sqlalchemy import ForeignKeyConstraint, UniqueConstraint, inspect

from app.db.base import Base
from app.models import Application, InterviewRound, User
from app.models.enums import ApplicationStatus, InterviewOutcome


def test_metadata_includes_core_tables() -> None:
    assert {"users", "applications", "interview_rounds"} <= set(Base.metadata.tables)


def test_user_columns_and_unique_email() -> None:
    table = User.__table__
    assert {column.name for column in table.columns} == {
        "id",
        "email",
        "hashed_password",
        "created_at",
    }
    unique_columns = {
        column.name
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
        for column in constraint.columns
    }
    assert "email" in unique_columns


def test_application_belongs_to_user() -> None:
    table = Application.__table__
    assert {column.name for column in table.columns} == {
        "id",
        "user_id",
        "company_name",
        "role_title",
        "status",
        "applied_date",
        "deadline",
        "notes",
        "job_description",
        "resume_version",
        "created_at",
        "updated_at",
    }
    foreign_keys = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    assert any(
        list(constraint.column_keys) == ["user_id"]
        and list(constraint.elements)[0].target_fullname == "users.id"
        for constraint in foreign_keys
    )


def test_interview_round_belongs_to_application() -> None:
    table = InterviewRound.__table__
    assert {column.name for column in table.columns} == {
        "id",
        "application_id",
        "round_name",
        "scheduled_at",
        "notes",
        "outcome",
    }
    foreign_keys = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    assert any(
        list(constraint.column_keys) == ["application_id"]
        and list(constraint.elements)[0].target_fullname == "applications.id"
        for constraint in foreign_keys
    )


def test_enum_values_match_product_spec() -> None:
    assert [status.value for status in ApplicationStatus] == [
        "Wishlist",
        "Applied",
        "OA",
        "Interviewing",
        "Offer",
        "Rejected",
    ]
    assert [outcome.value for outcome in InterviewOutcome] == [
        "Pending",
        "Passed",
        "Failed",
    ]


def test_relationships_are_configured() -> None:
    assert User.applications.property.mapper.class_ is Application
    assert Application.user.property.mapper.class_ is User
    assert Application.interview_rounds.property.mapper.class_ is InterviewRound
    assert InterviewRound.application.property.mapper.class_ is Application


def test_inspect_does_not_require_a_live_database() -> None:
    inspector = inspect(Application)
    assert inspector.persist_selectable.name == "applications"
