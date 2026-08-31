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

Stages 1–12 cover the project foundation, database, authentication, application tracking, interviews, analytics, UI, the AI provider abstraction, standalone resume ATS analysis, and resume-to-job-description matching. Later stages add more AI features and deployment.

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

## Documentation

- `BUILD_SPEC.md` — staged build specification
- `DECISIONS.md` — architectural decisions and tradeoffs
- `backend/README.md` — backend setup
- `frontend/README.md` — frontend setup
