from pathlib import Path

from app.core.config import DEV_JWT_SECRET

REPO_ROOT = Path(__file__).resolve().parents[2]
PROD_COMPOSE = REPO_ROOT / "docker-compose.prod.yml"
PROD_ENV_EXAMPLE = REPO_ROOT / ".env.production.example"


def _compose_text() -> str:
    return PROD_COMPOSE.read_text(encoding="utf-8")


def test_production_compose_does_not_publish_postgres_or_redis() -> None:
    text = _compose_text()

    assert "ENVIRONMENT: production" in text
    assert '"8000:8000"' in text
    assert '"80:80"' in text
    assert "JWT_SECRET: ${JWT_SECRET:?JWT_SECRET must be set}" in text
    assert "5432:" not in text.replace("postgres:5432", "")
    assert "6379:" not in text.replace("redis:6379", "")
    assert "2375:" not in text
    assert "2376:" not in text


def test_production_compose_restarts_and_does_not_embed_secrets() -> None:
    text = _compose_text()

    assert text.count("restart: unless-stopped") == 4
    assert text.count("no-new-privileges:true") == 4
    assert DEV_JWT_SECRET not in text
    assert "AI_API_KEY: ${AI_API_KEY:-}" in text
    assert "sk-" not in text
    assert "AIza" not in text


def test_production_env_example_rejects_development_jwt_placeholder() -> None:
    text = PROD_ENV_EXAMPLE.read_text(encoding="utf-8")
    jwt_line = next(
        line for line in text.splitlines() if line.startswith("JWT_SECRET=")
    )
    secret = jwt_line.split("=", 1)[1].strip()

    assert secret != DEV_JWT_SECRET
    assert len(secret) >= 32
    assert "AI_API_KEY=" in text
    assert "VITE_API_BASE_URL=http://YOUR_EC2_PUBLIC_IP:8000" in text
    assert "CORS_ORIGINS=http://YOUR_EC2_PUBLIC_IP" in text
