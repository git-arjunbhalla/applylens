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

## Docker (local Compose)

When the API runs in Docker Compose, PostgreSQL and Redis are sibling services (`postgres`, `redis`). `DATABASE_URL` and `REDIS_URL` must use those hostnames, not `localhost`. Compose sets them; do not bake secrets into the image.

From the repository root:

```powershell
copy .env.example .env
docker compose up -d --build
```

The backend image runs `alembic upgrade head` on start, then uvicorn on `0.0.0.0:8000`. Healthcheck: `GET /health`. Redis is not persisted; it only stores AI rate-limit counters.

This is local infrastructure, not production or AWS deployment.

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

The default suite uses an in-memory SQLite database, a fake Redis rate-limit backend, and a mocked AI client. It does not require PostgreSQL, Redis, or a Gemini API key. Ownership, authentication, PDF validation, and AI failure mapping are covered in `backend/tests/`.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `APP_NAME` | API title |
| `ENVIRONMENT` | `development` or `production` |
| `DEBUG` | Enables SQLAlchemy echo logging when true |
| `DATABASE_URL` | Async PostgreSQL URL (`postgresql+asyncpg://...`) |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins |
| `JWT_SECRET` | Secret used to sign access and refresh tokens |
| `JWT_ALGORITHM` | JWT signing algorithm (`HS256`) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime in minutes |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh-token lifetime in days |
| `AI_PROVIDER` | AI backend (`gemini` is the only implemented provider) |
| `AI_API_KEY` | Gemini API key (backend only; never expose to the frontend) |
| `AI_MODEL` | Gemini model name (default `gemini-3.6-flash`) |
| `AI_TIMEOUT_SECONDS` | Provider request timeout in seconds |
| `REDIS_URL` | Redis connection URL for AI rate-limit counters only |
| `AI_RATE_LIMIT_REQUESTS` | Max AI requests per user per window (default 10) |
| `AI_RATE_LIMIT_WINDOW_SECONDS` | Rate-limit window in seconds (default 3600) |

AI calls are made only from FastAPI through `app.services.ai_client`. React must not call Gemini and must not receive `AI_API_KEY`.

Authenticated AI endpoints (`/ai/resume-analysis`, `/ai/jd-match`, `/ai/cover-letter`) share one per-user quota: **10 requests per hour**, stored in Redis as `ratelimit:ai:{user_id}:{window}` with a TTL for the remainder of the hour. Exceeding the quota returns HTTP 429. If Redis is down, the limiter fails open (the request proceeds) and the failure is logged without exposing Redis details. PostgreSQL remains the source of truth.

Local Redis (optional for development; required for the limiter to enforce quotas):

```powershell
docker run --name applylens-redis -p 6379:6379 -d redis:7-alpine
```

Resume analysis: `POST /api/v1/ai/resume-analysis` (authenticated, `multipart/form-data`). Upload a resume PDF as `resume`. The backend extracts text in memory and returns a standalone ATS/resume-quality result (`ats_score`, `score_breakdown`, strengths, issues, suggestions). No job description is accepted. The PDF is not stored.

Job description match: `POST /api/v1/ai/jd-match` (authenticated, `multipart/form-data`). Upload a resume PDF as `resume` and the job text as `job_description`. The backend extracts PDF text in memory with PyMuPDF (limit 5 MB) and returns keyword overlap (`matched_keywords`, `missing_keywords`, `relevant_skills`, `important_requirements`, `match_score`). The PDF and extracted text are not stored.

Cover letter: `POST /api/v1/ai/cover-letter` (authenticated, `multipart/form-data`). Upload a resume PDF as `resume` plus `job_description`, `company`, and `role`. The backend reuses the same in-memory PDF extraction and returns `{ "cover_letter": "..." }`. The letter is a draft grounded only in the supplied resume and job description; it is not stored.

Optional live check (not part of the default test suite):

```powershell
$env:APPLYLENS_LIVE_GEMINI="1"
pytest tests/test_ai_client.py -k live_gemini
```
