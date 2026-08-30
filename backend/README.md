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

4. Start the API:

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

PostgreSQL is not required for the health endpoint. Database models and migrations are added in Stage 2.

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
