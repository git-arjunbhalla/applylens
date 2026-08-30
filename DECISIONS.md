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

## Stage 2 — Database

### Integer primary keys

`User`, `Application`, and `InterviewRound` use autoincrement integers instead of UUIDs. Integer keys are easier to inspect, join, and explain. UUIDs can be introduced later if public ID leakage becomes a concern.

### String-backed enums, not native PostgreSQL enums

Application status and interview outcome are Python `str` enums stored as `VARCHAR`. Native PostgreSQL enum types make later value changes painful in Alembic. Validation still happens in SQLAlchemy using the spec values (`Wishlist`, `Applied`, `OA`, `Interviewing`, `Offer`, `Rejected` and `Pending`, `Passed`, `Failed`).

### Declarative `Base` is separate from the async engine

`Base` lives in `app/db/base.py`. Alembic imports models and metadata without constructing the async SQLAlchemy engine. That keeps `alembic upgrade` usable even when `DATABASE_URL` is a sync URL used only for migration tests.

### Alembic uses a synchronous driver

The app engine stays on `asyncpg`. Alembic converts `postgresql+asyncpg://` to `postgresql+psycopg://` so migrations can use SQLAlchemy's sync `Engine`. `psycopg[binary]` is the sync driver for that path.

### `updated_at` is ORM-maintained

`Application.updated_at` uses a server default of `CURRENT_TIMESTAMP` and SQLAlchemy `onupdate=func.now()`. There is no PostgreSQL trigger. Raw SQL updates will not refresh the timestamp.

### Cascade deletes

Foreign keys use `ON DELETE CASCADE` so deleting a user removes their applications, and deleting an application removes its interview rounds. Ownership checks are still required in the API layer (Stage 4+).

### Migration tests without a live PostgreSQL

This environment did not have PostgreSQL listening on localhost. The Alembic upgrade/downgrade test applies the initial revision to a temporary SQLite database. Production and local development still target PostgreSQL.

## Stage 3 — Authentication

### Stateless JWT refresh tokens

Access and refresh tokens are both signed JWTs. They are not stored in the database. This keeps Stage 3 small and avoids a token table before there is a logout/revocation requirement. Individual tokens cannot be revoked until they expire, unless `JWT_SECRET` is rotated.

### Separate token types

Every token includes a `type` claim (`access` or `refresh`). Protected routes accept only access tokens. `/auth/refresh` accepts only refresh tokens. Signature, expiration, `sub`, and `type` are all validated.

### bcrypt without Passlib

Passwords are hashed with the `bcrypt` package directly. Passlib was skipped to avoid its known bcrypt-backend version conflicts and to keep the hashing code easy to read.

### Signup returns tokens

Successful signup returns the same token payload as login so a new user is authenticated immediately. Password hashes are never included in responses.

### Shared login error

Unknown emails and incorrect passwords both return `401` with `Invalid email or password` so the API does not reveal whether an email is registered.

### Auth tests use in-memory SQLite

Authentication tests override `get_db` with `sqlite+aiosqlite:///:memory:`. That matches the Stage 2 decision to keep automated tests runnable without a live PostgreSQL instance. Development and production still use PostgreSQL.
