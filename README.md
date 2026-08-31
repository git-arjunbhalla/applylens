# ApplyLens

ApplyLens is an AI-powered job and internship application tracker.

This repository is a monorepo:

```
React (Vite)
  ↓
FastAPI
  ↓
SQLAlchemy
  ↓
PostgreSQL
```

Stages 1–16 cover the project foundation, database, authentication, application tracking, interviews, analytics, UI, the AI provider abstraction, standalone resume ATS analysis, resume-to-job-description matching, AI cover-letter drafts, Redis-backed per-user AI rate limiting, a testing/security review, and local Docker Compose infrastructure. Later stages add CI/CD and deployment. This Docker setup is for local infrastructure only; it is not an AWS or production deployment.

## Local setup

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Health check: `http://localhost:8000/health`

### Frontend

```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```

App: `http://localhost:5173`

## Docker (local infrastructure)

Docker Compose runs frontend, backend, PostgreSQL, and Redis together. Postgres and Redis are not published to the host. Redis is ephemeral (AI rate-limit counters only). PostgreSQL data uses a named volume.

Copy the Compose example env file and start the stack from the repo root:

```powershell
copy .env.example .env
docker compose build
docker compose up -d
```

| Service | Host URL | Notes |
| --- | --- | --- |
| Frontend | `http://localhost:8080` | nginx serving the Vite production build |
| Backend | `http://localhost:8000` | FastAPI; `/health` is `{"status":"ok"}` |
| PostgreSQL | Compose network only | hostname `postgres` |
| Redis | Compose network only | hostname `redis`; not persisted |

Stop, logs, rebuild, and cleanup:

```powershell
docker compose stop
docker compose logs -f
docker compose up -d --build
docker compose down
docker compose down -v
```

`down -v` deletes the Postgres volume. The backend container runs `alembic upgrade head` on start. Put a Gemini key in the root `.env` as `AI_API_KEY` only if you need live AI calls; never put it in frontend env files.

## Documentation

- `BUILD_SPEC.md` — staged build specification
- `DECISIONS.md` — architectural decisions and tradeoffs
- `backend/README.md` — backend setup
- `frontend/README.md` — frontend setup
