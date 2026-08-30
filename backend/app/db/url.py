def to_sync_database_url(url: str) -> str:
    """Convert an async SQLAlchemy URL to a sync URL for Alembic.

    The application uses asyncpg (and may later use aiosqlite in tests).
    Alembic's default online runner uses a synchronous Engine.
    """
    replacements = (
        ("postgresql+asyncpg://", "postgresql+psycopg://"),
        ("sqlite+aiosqlite://", "sqlite://"),
    )
    for async_prefix, sync_prefix in replacements:
        if url.startswith(async_prefix):
            return sync_prefix + url[len(async_prefix) :]
    return url
