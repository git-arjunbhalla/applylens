# Decisions

Architectural choices and tradeoffs made during development.

## Stage 1 — Project foundation

### Monorepo layout

The repository follows the `BUILD_SPEC.md` structure: `backend/` and `frontend/` as sibling projects. This keeps local development simple without introducing Docker or extra workspace tooling.

### Environment configuration

Backend settings use Pydantic Settings v2 so environment variables are validated in one place. Frontend public config uses `VITE_API_BASE_URL`. Real `.env` files are gitignored; only `.env.example` files are committed.

### Database foundations without models

Stage 1 creates the async SQLAlchemy engine, session factory, and declarative `Base`. Models, relationships, and the first Alembic migration are deferred to Stage 2 so the API can start without a live PostgreSQL connection.

The `/health` endpoint does not query the database. That keeps the Stage 1 smoke check independent of database availability.

### Alembic initialized, no migrations yet

Alembic is initialized so the migration layout exists. The first schema revision is created in Stage 2 after models exist.

### Axios for the API client

The frontend uses Axios instead of `fetch` because later stages need request interceptors for JWT access/refresh handling. A thin `src/services/api.js` wrapper is the only client setup in Stage 1.

### Tailwind CSS v4 via the Vite plugin

Tailwind is installed with `@tailwindcss/vite` rather than the older PostCSS/v3 setup. This matches current Vite tooling and avoids extra config files. The ApplyLens visual identity is not implemented in Stage 1.

### JavaScript frontend

The spec lists React, Vite, Tailwind, React Router, and Axios. TypeScript was not added so the frontend stays closer to the required stack.
