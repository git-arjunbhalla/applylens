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

## Environment variables

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Backend origin, e.g. `http://localhost:8000` |

## Scripts

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the Vite development server |
| `npm run build` | Production build |
| `npm run preview` | Preview the production build |
| `npm test` | Run frontend tests |
