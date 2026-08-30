# ApplyLens Backend

FastAPI service for ApplyLens.

## Local setup

1. Create and activate a virtual environment from this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy the example environment file and adjust values if needed:

```powershell
copy .env.example .env
```

4. Apply database migrations (PostgreSQL must be running and `DATABASE_URL` must point at it):

```powershell
alembic upgrade head
```

5. Start the API:

```powershell
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Health check

```powershell
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

PostgreSQL is not required for the health endpoint.

## Database

ApplyLens uses PostgreSQL in development and production. Alembic owns the schema.

```powershell
alembic upgrade head
```

Roll back the latest revision:

```powershell
alembic downgrade -1
```

The app uses `postgresql+asyncpg://` for SQLAlchemy. Alembic converts that URL to `postgresql+psycopg://` because migrations run on a synchronous engine.

## Tests

```powershell
pytest
```

## Environment variables

| Variable | Purpose |
| --- | --- |
| `APP_NAME` | API title |
| `ENVIRONMENT` | `development` or `production` |
| `DEBUG` | Enables SQLAlchemy echo logging when true |
| `DATABASE_URL` | Async PostgreSQL URL (`postgresql+asyncpg://...`) |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins |
