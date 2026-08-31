# ApplyLens Frontend

React + Vite client for ApplyLens.

## Local setup

```powershell
copy .env.example .env
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

Authentication, application tracking, standalone resume ATS analysis, job-description matching, and AI cover-letter drafts are implemented. Analyze, JD Match, and Cover letter all call FastAPI only; the Gemini key is never sent to the browser.

## Docker (local Compose)

The frontend image is a multi-stage build: Node compiles the Vite app, then nginx serves `dist`. The browser still calls FastAPI at `VITE_API_BASE_URL` (default `http://localhost:8000`). That value is public and is the only Vite env var. Do not pass backend secrets as `VITE_*` build args.

From the repository root:

```powershell
copy .env.example .env
docker compose up -d --build
```

The Compose frontend is `http://localhost:8080`. CORS on the backend must allow that origin (Compose sets `CORS_ORIGINS`).

This is local infrastructure, not production or AWS deployment.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Backend origin, e.g. `http://localhost:8000` |

## Scripts

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the Vite development server |
| `npm run build` | Production build (also used to verify the frontend for Stage 15) |
| `npm run preview` | Preview the production build |
| `npm test` | Run frontend tests |

GitHub Actions (`.github/workflows/ci.yml`) runs `npm ci`, `npm test`, and `npm run build` on pushes and pull requests to `main`. CI does not deploy.
