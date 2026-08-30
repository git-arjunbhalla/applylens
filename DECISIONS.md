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

## Stage 4 — Application CRUD

### Ownership is enforced in the query, not only in the response

Every application query includes `user_id = current_user.id`. Get, update, and delete use that same owned-row lookup. Missing IDs and other users' IDs both return `404 Application not found` so the API does not confirm that another user's record exists.

### List filtering and sorting happen in SQL

Pagination (`page`, `page_size`), sorting, status, company, deadline range, and search are applied in SQLAlchemy before `LIMIT`/`OFFSET`. The list handler does not load a user's full application set into memory.

### Search vs company filter

`search` is a case-insensitive substring match against `company_name` or `role_title`. `company` is a case-insensitive exact match on `company_name`. LIKE wildcards in search text are escaped. Notes and job descriptions are not searched in this stage.

### PUT is a partial update

`PUT /applications/{id}` updates only the fields present in the request body. An empty body is rejected. This avoids forcing clients to resend the full application for a status or notes change.

### Default list order

The default sort is `created_at` descending, with `id` as a stable tiebreaker. Null deadlines sort last.

## Stage 5 — Interview-round tracking

### Ownership is checked through the parent application

Interview queries join `interview_rounds` to `applications` and require `applications.user_id = current_user.id`. List and create first confirm the application is owned. Missing applications and other users' applications both return `404 Application not found`. A missing round on an owned application returns `404 Interview round not found`. That keeps User A from learning whether User B's application or interview exists.

### PUT is a partial update

`PUT /applications/{application_id}/interviews/{id}` updates only the fields present in the request body, matching Stage 4 application updates. An empty body is rejected.

### List is unpaginated

Interview lists are not paginated. A single application has a small number of rounds, so the handler returns a JSON array ordered by `scheduled_at` ascending (unscheduled last), then `id`.

### `scheduled_at` must be timezone-aware

`InterviewRound.scheduled_at` is stored as `DateTime(timezone=True)`. Create and update reject naive datetimes so interview times are not ambiguous across environments.

SQLite test storage drops timezone info. The public schema treats a naive stored value as UTC on serialize so API responses stay timezone-aware. PostgreSQL keeps `timestamptz` as stored.

## Stage 6 — Analytics API

### Upcoming deadlines use an inclusive UTC date window

`upcoming_deadlines` counts owned applications whose `deadline` is on or after today's UTC date and on or before today + 7 calendar days. Today is included because a deadline due today is still upcoming. Null deadlines and past dates are excluded. `deadline` is a date-only field, so the window is calendar dates in UTC rather than a local timezone or a 7×24-hour rolling interval.

### Response rate is status-based, not timestamp-based

Response rate is `(OA + Interviewing + Offer + Rejected) / (total − Wishlist)`. Wishlist is excluded from the denominator because those applications have not been submitted. `Applied` is submitted but not a response. When the denominator is zero, the rate is `0.0`. Interview-round outcomes are not used for this metric.

### Offers and rejections are application statuses

`offers` and `rejections` count applications with status `Offer` and `Rejected`. Interview outcomes (`Passed` / `Failed`) are not treated as application-level offers or rejections.

### Interview count is round rows, not applications

`interview_count` is `COUNT(interview_rounds)` for the user's applications, not distinct applications. Aggregation starts from `interview_rounds` joined to owned applications so a round-heavy application cannot inflate `total_applications`.

### Average time-to-response is not calculated

The schema has `applied_date` but no response timestamp. `updated_at` changes on any edit, and interview `scheduled_at` is time-to-interview, not time-to-response. The field is returned as `null` rather than approximating from unreliable columns. No schema change was added to invent this metric.

## Stage 7 — Frontend authentication

### Access token stays in memory; refresh token uses localStorage

The backend issues stateless JWTs in JSON and does not set httpOnly cookies. Switching to cookie-based auth would have required a backend redesign. For the MVP, the access token is kept only in module memory and attached by the Axios interceptor. The refresh token is stored in `localStorage` under `applylens.refresh_token` so a page reload can restore the session.

This is an XSS tradeoff: script on the origin could read the refresh token. The access token is short-lived (15 minutes) and is not persisted, which limits the window if memory is dumped but does not protect against XSS. httpOnly cookies would be the more secure long-term option.

### Session restore uses refresh then `/auth/me`

On startup, if a refresh token is present, the client calls `POST /api/v1/auth/refresh`, stores the new tokens, then `GET /api/v1/auth/me` to load the current user. AuthContext treats that user object as the source of truth. Tokens are not placed in React context.

### Axios interceptor refresh, single-flight

A 401 on an authenticated request triggers one refresh. Concurrent 401s share the same in-flight refresh promise. Login, signup, and refresh requests do not enter that path, which prevents an infinite refresh loop. A failed refresh clears tokens and notifies AuthContext so protected routes return to login.

### Logout is client-side only

Refresh tokens are stateless JWTs. There is no backend revoke endpoint. Logout clears memory and `localStorage` and drops React auth state.

### Minimal protected home

`/` is a protected landing page with the current email and a logout button. Login and signup are guest-only. This is enough to exercise the auth flow; the application dashboard belongs to Stage 8.

## Stage 8 — Application UI

### Dashboard recent activity uses the applications list API

`GET /api/v1/analytics/summary` does not return an activity feed. The dashboard shows summary metrics from that endpoint and loads the five most recently updated applications with `GET /api/v1/applications?sort=updated_at&order=desc&page_size=5`. No extra analytics are computed on the client. `average_time_to_response_days` is shown as “Not available” when the API returns `null`.

### Filters and pagination stay on the server

The applications page sends `page`, `page_size`, `sort`, `order`, `status`, `company`, `deadline_before`, `deadline_after`, and `search` as query parameters. Search and company inputs are debounced (300ms) so typing does not fire a request per keystroke. The client does not paginate or filter a full in-memory dataset.

### PUT bodies contain only changed fields

Application and interview edits send a partial body matching the backend’s unset-field semantics. Unchanged fields are omitted so a notes or status edit cannot overwrite other columns. Blank optional text is sent as `null` when the user cleared a previously filled field.

### Interview state lives in the detail page, not the application record

Interview rounds are loaded from the nested interview endpoints and are not copied into application list/detail payloads. Destructive deletes use an in-page confirmation dialog; there is no soft-delete API.

### No extra state-management library

Stage 8 keeps React local state, the existing AuthContext, and the Stage 7 Axios client. Dashboard and list screens refetch on mount so returning from create/edit/delete shows current data without a global cache.

## Stage 9 — UI polish

### Theme persistence is localStorage, not a user-profile API

Theme preference is stored under `applylens.theme` (`light` or `dark`). When nothing is stored, the client follows `prefers-color-scheme`. A small inline script in `index.html` applies the class before React hydrates to avoid a flash. Theme is not sent to the backend; there is no user settings endpoint.

### Recharts for status counts only

The dashboard chart plots `counts_by_status` from `GET /api/v1/analytics/summary`. No client-side metrics were invented and the analytics API was not changed. The existing status list remains so the same data stays readable without the chart.

### Shared presentational components, no design-system package

Buttons, fields, cards, alerts, page chrome, and the brand mark are small local components. Tailwind v4 tokens in `index.css` define light and dark palettes around fluorescent orange, cream, and charcoal. Google Fonts (Fraunces + Source Sans 3) are linked from `index.html` rather than adding a font package.
