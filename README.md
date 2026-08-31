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

Stages 1–17 cover the project foundation, database, authentication, application tracking, interviews, analytics, UI, the AI provider abstraction, standalone resume ATS analysis, resume-to-job-description matching, AI cover-letter drafts, Redis-backed per-user AI rate limiting, a testing/security review, local Docker Compose infrastructure, and GitHub Actions CI. Stage 18 will handle deployment. This Docker setup is for local infrastructure only; it is not an AWS or production deployment. CI validates the repository; it does not deploy.

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

## Continuous integration

GitHub Actions (`.github/workflows/ci.yml`) runs on pushes to `main` and on pull requests targeting `main`. A change is ready when all three jobs pass:

| Job | What it checks |
| --- | --- |
| Backend tests | Installs Python 3.12 dependencies and runs `pytest` |
| Frontend tests | `npm ci`, Vitest (`npm test`), and the Vite production build |
| Docker build | `docker compose config`, then `docker compose build` for the backend and frontend images |

CI uses in-memory SQLite, a fake AI client, and a fake Redis rate-limit backend. It does not call Gemini, does not need AWS credentials, and does not start the Compose stack. Secrets such as `AI_API_KEY` and `JWT_SECRET` are not stored in the workflow.

This pipeline validates and builds the application. It does not deploy. AWS and other production hosting are out of scope until Stage 18.

## Documentation

- `BUILD_SPEC.md` — staged build specification
- `DECISIONS.md` — architectural decisions and tradeoffs
- `backend/README.md` — backend setup
- `frontend/README.md` — frontend setup
