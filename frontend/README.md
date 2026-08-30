# ApplyLens Frontend

React + Vite client for ApplyLens.

## Local setup

```powershell
copy .env.example .env
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

The Stage 1 UI is a technical shell only. Visual identity, authentication, and product pages are added in later stages.

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
