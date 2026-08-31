import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Application, InterviewRound, User  # noqa: F401
from app.services.rate_limit import AIRateLimiter, get_ai_rate_limiter


class FakeRateLimitBackend:
    """In-memory INCR+TTL stand-in so tests never need a Redis server."""

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.counts: dict[str, int] = {}
        self.ttls: dict[str, int] = {}

    async def incr_with_expire(self, key: str, ttl_seconds: int) -> int:
        if self.fail:
            raise ConnectionError("Redis is unavailable")
        if key not in self.counts:
            self.counts[key] = 0
            self.ttls[key] = ttl_seconds
        self.counts[key] += 1
        return self.counts[key]

    async def aclose(self) -> None:
        return None


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def setup() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(setup())

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    rate_backend = FakeRateLimitBackend()
    limiter = AIRateLimiter(
        rate_backend,
        max_requests=settings.ai_rate_limit_requests,
        window_seconds=settings.ai_rate_limit_window_seconds,
    )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_ai_rate_limiter] = lambda: limiter

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

    async def teardown() -> None:
        await engine.dispose()

    asyncio.run(teardown())
