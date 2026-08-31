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

Stages 1–18 cover the project foundation, database, authentication, application tracking, interviews, analytics, UI, the AI provider abstraction, standalone resume ATS analysis, resume-to-job-description matching, AI cover-letter drafts, Redis-backed per-user AI rate limiting, a testing/security review, local Docker Compose infrastructure, GitHub Actions CI, and AWS EC2 deployment preparation. Local Compose is for development. Production uses `docker-compose.prod.yml` on a single EC2 instance. CI validates the repository; it does not deploy to AWS. This repository has not been verified as a live AWS deployment.

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
| Docker build | `docker compose config` for local and production files, then `docker compose build` |

CI uses in-memory SQLite, a fake AI client, and a fake Redis rate-limit backend. It does not call Gemini, does not need AWS credentials, and does not start the Compose stack. Secrets such as `AI_API_KEY` and `JWT_SECRET` are not stored in the workflow.

This pipeline validates and builds the application. It does not deploy.

## AWS (EC2, ap-south-1)

Production target is **one Ubuntu EC2 instance** in **ap-south-1** running Docker Compose: nginx frontend (host port 80), FastAPI (host port 8000), PostgreSQL, and Redis. Postgres and Redis use Compose DNS (`postgres`, `redis`) and are not published. Redis remains ephemeral rate-limit storage. PostgreSQL uses the `postgres_data` named volume.

Recommended instance: Ubuntu Server 24.04 LTS **x86_64**, **t3.micro**, 20–30 GiB gp3. Security group: SSH from your IP, 80 and 8000 from the internet; never 5432, 6379, or the Docker daemon. Create secrets in a gitignored `.env` on the host from `.env.production.example`.

Exact SSH, Docker install, clone, env, build, health, logs, restart, stop, and cleanup commands: [`docs/aws-ec2-deployment.md`](docs/aws-ec2-deployment.md). AWS console launch, key pair, security group, and Elastic IP are **manual steps**. Terminating the instance can destroy Postgres data unless the volume is snapshotted.

```bash
cp .env.production.example .env
# edit .env on the EC2 host only
docker compose --env-file .env -f docker-compose.prod.yml up -d --build
curl http://127.0.0.1:8000/health
```

`VITE_API_BASE_URL` must be the public API origin (`http://<public-ip>:8000`) and must not contain secrets. `CORS_ORIGINS` must be the frontend origin (`http://<public-ip>`). `AI_API_KEY` stays on the backend.

## Documentation

- `BUILD_SPEC.md` — staged build specification
- `DECISIONS.md` — architectural decisions and tradeoffs
- `docs/aws-ec2-deployment.md` — EC2, security group, Compose production, and operations
- `backend/README.md` — backend setup
- `frontend/README.md` — frontend setup
