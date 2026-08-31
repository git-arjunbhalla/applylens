import asyncio

import pytest
from sqlalchemy import event, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.models import Application, InterviewRound, User
from app.models.enums import ApplicationStatus, InterviewOutcome


def _session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async def setup() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(setup())
    return engine, factory


@pytest.fixture
def db_factory():
    engine, factory = _session_factory()
    yield factory

    async def teardown() -> None:
        await engine.dispose()

    asyncio.run(teardown())


def test_duplicate_email_is_rejected(db_factory) -> None:
    async def run() -> None:
        async with db_factory() as session:
            session.add(
                User(email="dup@example.com", hashed_password=hash_password("password123"))
            )
            await session.commit()
            session.add(
                User(email="dup@example.com", hashed_password=hash_password("otherpass1"))
            )
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()

            count = await session.scalar(select(User).where(User.email == "dup@example.com"))
            assert count is not None
            users = (await session.execute(select(User))).scalars().all()
            assert len(users) == 1

    asyncio.run(run())


def test_application_requires_existing_user(db_factory) -> None:
    async def run() -> None:
        async with db_factory() as session:
            session.add(
                Application(
                    user_id=9999,
                    company_name="Acme",
                    role_title="Engineer",
                    status=ApplicationStatus.WISHLIST,
                )
            )
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()
            assert (await session.scalar(select(Application))) is None

    asyncio.run(run())


def test_interview_requires_existing_application(db_factory) -> None:
    async def run() -> None:
        async with db_factory() as session:
            session.add(
                InterviewRound(
                    application_id=9999,
                    round_name="Phone screen",
                    outcome=InterviewOutcome.PENDING,
                )
            )
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()
            assert (await session.scalar(select(InterviewRound))) is None

    asyncio.run(run())


def test_deleting_application_removes_interview_rounds(db_factory) -> None:
    async def run() -> None:
        async with db_factory() as session:
            user = User(email="owner@example.com", hashed_password=hash_password("password123"))
            session.add(user)
            await session.flush()
            application = Application(
                user_id=user.id,
                company_name="Acme",
                role_title="Engineer",
                status=ApplicationStatus.WISHLIST,
            )
            session.add(application)
            await session.flush()
            session.add(
                InterviewRound(
                    application_id=application.id,
                    round_name="Phone screen",
                    outcome=InterviewOutcome.PENDING,
                )
            )
            await session.commit()

            loaded = await session.get(Application, application.id)
            assert loaded is not None
            await session.delete(loaded)
            await session.commit()

            assert (await session.scalar(select(InterviewRound))) is None
            assert (await session.get(User, user.id)) is not None

    asyncio.run(run())


def test_transaction_rollback_does_not_persist_application(db_factory) -> None:
    async def run() -> None:
        async with db_factory() as session:
            user = User(email="owner@example.com", hashed_password=hash_password("password123"))
            session.add(user)
            await session.commit()
            user_id = user.id

            session.add(
                Application(
                    user_id=user_id,
                    company_name="Should Not Persist",
                    role_title="Engineer",
                    status=ApplicationStatus.APPLIED,
                )
            )
            await session.flush()
            await session.rollback()

            remaining = (
                await session.execute(select(Application).where(Application.user_id == user_id))
            ).scalars().all()
            assert remaining == []

            persisted_user = await session.scalar(select(User.id).where(User.email == "owner@example.com"))
            assert persisted_user == user_id
            await session.execute(text("SELECT 1"))

    asyncio.run(run())
