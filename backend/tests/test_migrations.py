from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _alembic_config() -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return config


def test_initial_migration_upgrades_and_downgrades(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'applylens.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    alembic_config = _alembic_config()
    command.upgrade(alembic_config, "head")

    engine = create_engine(database_url)
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    assert {"users", "applications", "interview_rounds", "alembic_version"} <= table_names

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    assert user_columns == {"id", "email", "hashed_password", "created_at"}

    application_fks = inspector.get_foreign_keys("applications")
    assert any(fk["referred_table"] == "users" for fk in application_fks)

    interview_fks = inspector.get_foreign_keys("interview_rounds")
    assert any(fk["referred_table"] == "applications" for fk in interview_fks)

    command.downgrade(alembic_config, "base")
    downgraded_tables = set(inspect(engine).get_table_names())
    assert "users" not in downgraded_tables
    assert "applications" not in downgraded_tables
    assert "interview_rounds" not in downgraded_tables


def test_sync_url_conversion() -> None:
    from app.db.url import to_sync_database_url

    assert (
        to_sync_database_url("postgresql+asyncpg://user:pass@localhost:5432/applylens")
        == "postgresql+psycopg://user:pass@localhost:5432/applylens"
    )
    assert to_sync_database_url("sqlite+aiosqlite:///./test.db") == "sqlite:///./test.db"
    assert (
        to_sync_database_url("postgresql+psycopg://user:pass@localhost:5432/applylens")
        == "postgresql+psycopg://user:pass@localhost:5432/applylens"
    )
