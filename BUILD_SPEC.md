# ApplyLens
## Staged Cursor Agent Build Specification

You are the senior software engineer helping me build a portfolio-quality full-stack application called **ApplyLens**.

The goal is to build and deploy a genuinely working AI-powered job/internship application tracker quickly, while keeping the codebase clean, understandable, maintainable, and suitable for explaining in technical interviews.

I am a beginner-to-intermediate developer learning Python backend development, so do not hide complexity unnecessarily and do not introduce technologies that are not required.

## ApplyLens Visual Identity

ApplyLens must have a distinctive, niche, modern editorial-tech aesthetic. It must not look like a generic AI SaaS dashboard.

### Color direction
- Signature accent: light/fluorescent orange.
- Do NOT use the common purple/blue AI gradient aesthetic.
- Use a sophisticated gradient palette built around fluorescent orange, warm amber, coral, cream, charcoal, and supporting neutrals.
- Use gradients selectively for hero areas, active states, charts, badges, focus states, and key CTAs.
- Do not put orange gradients behind every card.
- Maintain strong contrast and accessibility in both themes.

### Motion
- Use subtle, purposeful animation for page transitions, card entrances, hover/focus states, buttons, progress indicators, charts, and modals.
- Keep animation fast and restrained.
- Respect `prefers-reduced-motion`.
- Avoid excessive particles, parallax, floating effects, spinning elements, or constant motion.

### Theme
- Provide a proper light mode and dark mode.
- Both themes must be intentionally designed, not simple color inversion.
- Preserve the fluorescent-orange ApplyLens identity in both themes.
- Persist the user's theme preference.
- Respect system preference when no preference has been saved.

### Logo and icon
Create an original SVG-based ApplyLens mark that directly relates to the name.
Conceptually combine a lens/focus element with an application/job-search concept, such as a stylized focus ring incorporating a check, document edge, or application signal.

Do NOT use generic robot heads, sparkles, brain icons, circuit graphics, generic briefcases, or a standard magnifying-glass icon as the brand identity.

The mark must work as a navbar logo, favicon, mobile icon, and GitHub/portfolio branding.


The project must be completed in stages.

---

# 0. NON-NEGOTIABLE RULES

## Product goal

Build a working AI-powered job/internship application tracker that allows a user to:

1. Create an account and log in.
2. Track job and internship applications.
3. Move applications through different stages.
4. Store job descriptions, notes, deadlines, and application information.
5. Track interview rounds.
6. View useful application analytics.
7. Analyze a resume against a job description using AI.
8. Compare resume keywords against a job description.
9. Generate an AI-assisted cover letter.
10. Deploy the application using free-tier services.

Prioritize a working, polished MVP over excessive features.

Do not add unnecessary functionality merely because it sounds impressive.

---

# 1. FIXED TECH STACK

Do not change the stack unless a technical limitation makes it genuinely necessary.

### Backend

- Python
- FastAPI
- SQLAlchemy 2.x with async support
- Alembic
- Pydantic v2
- PostgreSQL
- pytest

### Frontend

- React
- Vite
- TailwindCSS
- React Router
- Axios or fetch
- Recharts or Chart.js

### Authentication

- JWT access tokens
- Refresh-token mechanism
- bcrypt-compatible password hashing

### AI

Use an abstraction layer:

`backend/app/services/ai_client.py`

Initial provider:

- Google Gemini API using its available free tier

The provider must be configurable through environment variables so another provider can be added later.

Never expose an AI API key to the frontend.

### Deployment

- Frontend: Vercel
- Backend: Render
- PostgreSQL: Neon free tier
- Source control: GitHub

Do not introduce Docker, Redis, Kubernetes, AWS, or other infrastructure unless there is a clear need.

---

# 2. CORE DATA MODEL

Start with these models only.

## User

- id
- email
- hashed_password
- created_at

## Application

- id
- user_id
- company_name
- role_title
- status
- applied_date
- deadline
- notes
- job_description
- resume_version
- created_at
- updated_at

Status values:

- Wishlist
- Applied
- OA
- Interviewing
- Offer
- Rejected

## InterviewRound

- id
- application_id
- round_name
- scheduled_at
- notes
- outcome

Outcome:

- Pending
- Passed
- Failed

Use proper foreign keys and relationships.

Every user's application data must be isolated from every other user's data.

---

# 3. PROJECT STRUCTURE

Use a clean monorepo:

applylens/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── context/
│   │   └── types/
│   ├── public/
│   ├── .env.example
│   └── README.md
│
├── README.md
├── DECISIONS.md
└── .gitignore

Do not create giant files.

Prefer small modules with clear responsibilities.

---

# 4. DEVELOPMENT PHILOSOPHY

The project will be developed through stages.

For every stage:

1. Inspect the existing repository before changing anything.
2. Understand the existing architecture.
3. Implement only the requested stage.
4. Do not rewrite working code unnecessarily.
5. Run tests.
6. Run the application when appropriate.
7. Fix errors before declaring the stage complete.
8. Give me a concise summary of:
   - what changed
   - files changed
   - commands used
   - tests performed
   - anything I need to manually verify
9. Update `DECISIONS.md` when an architectural decision or tradeoff is made.
10. Do not proceed to the next stage automatically.

At the end of every stage, stop.

Do not overwhelm me with explanations unless I ask for them.

---

# STAGE 1: PROJECT FOUNDATION

Goal:

Create the initial repository structure and development environment.

Tasks:

### Backend

Set up:

- FastAPI
- SQLAlchemy async
- Pydantic v2
- Alembic
- PostgreSQL configuration
- environment-variable configuration
- CORS configuration
- `/health` endpoint

Create:

GET /health

It should return a simple successful response.

### Frontend

Set up:

- Vite
- React
- TailwindCSS
- React Router
- Axios or fetch

Create a basic application shell.

### Configuration

Create `.env.example` for frontend and backend.

Never create or commit real secrets.

### Documentation

Create:

- README.md
- DECISIONS.md
- .gitignore

### Validation

Run the backend and frontend.

Confirm:

- backend starts
- frontend starts
- `/health` works
- frontend can load

STOP after completing Stage 1.

---

# STAGE 2: DATABASE

Goal:

Create the database layer.

Implement:

- database connection
- async SQLAlchemy engine
- session management
- User model
- Application model
- InterviewRound model
- relationships
- enums
- timestamps
- foreign keys

Configure Alembic.

Create the initial migration.

Test that the migration can be applied successfully.

Do not create unnecessary tables.

STOP after completing Stage 2.

---

# STAGE 3: AUTHENTICATION

Goal:

Implement secure but understandable authentication.

Create:

POST /api/v1/auth/signup
POST /api/v1/auth/login
POST /api/v1/auth/refresh

Requirements:

- password hashing
- JWT access tokens
- refresh tokens
- token expiration
- Pydantic validation
- appropriate HTTP status codes
- consistent error responses
- protected-route dependency

Do not store plaintext passwords.

Do not expose password hashes.

Create a simple protected test endpoint.

Write tests for:

- signup
- duplicate signup
- login
- incorrect password
- protected endpoint
- invalid token

Keep the authentication implementation understandable.

Document important security decisions in DECISIONS.md.

STOP after completing Stage 3.

---

# STAGE 4: APPLICATION CRUD

Goal:

Build the core of the product.

Create:

GET    /api/v1/applications
POST   /api/v1/applications
GET    /api/v1/applications/{id}
PUT    /api/v1/applications/{id}
DELETE /api/v1/applications/{id}

Requirements:

- authentication required
- user ownership enforcement
- Pydantic schemas
- validation
- proper 404 handling
- consistent error responses
- pagination where appropriate
- sorting
- search
- filtering

Support:

status
company
deadline_before
deadline_after
search

Make sure User A can never access User B's applications.

Write meaningful pytest coverage.

STOP after completing Stage 4.

---

# STAGE 5: INTERVIEW TRACKING

Goal:

Allow users to track interview rounds for applications.

Create nested endpoints such as:

GET    /applications/{application_id}/interviews
POST   /applications/{application_id}/interviews
PUT    /applications/{application_id}/interviews/{id}
DELETE /applications/{application_id}/interviews/{id}

Ensure ownership checks propagate from:

User → Application → InterviewRound.

Add validation for:

- round name
- scheduled time
- outcome

Write tests.

STOP after completing Stage 5.

---

# STAGE 6: ANALYTICS API

Goal:

Create useful analytics without overengineering.

Create:

GET /api/v1/analytics/summary

Return:

- total applications
- counts by status
- upcoming deadlines within 7 days
- number of interviews
- offers
- rejections
- response rate
- average time-to-response if sufficient data exists

If a metric cannot be calculated reliably from the current schema, do not invent data.

Return sensible zero/null values.

Write tests.

STOP after completing Stage 6.

---

# STAGE 7: FRONTEND AUTHENTICATION

Goal:

Connect React to the backend.

Create:

- Login page
- Signup page
- authentication state
- protected routes
- logout
- API client
- authentication error handling

Implement the access-token/refresh-token flow.

Avoid unnecessary localStorage usage for sensitive credentials.

If a practical MVP tradeoff requires localStorage, document the reason and security tradeoff in DECISIONS.md.

Do not build the entire UI yet.

STOP after completing Stage 7.

---

# STAGE 8: APPLICATION UI

Goal:

Create the main usable application.

Build:

### Dashboard

Show:

- application count
- status breakdown
- upcoming deadlines
- interview count
- offer count
- useful recent activity

### Applications page

Include:

- application list
- search
- filters
- sorting
- status
- company
- role
- deadline

### Create/Edit application

Allow:

- company
- role
- status
- applied date
- deadline
- notes
- job description
- resume version

### Application detail

Show:

- application information
- job description
- notes
- interview rounds
- status
- deadlines

Implement:

- loading states
- empty states
- error states
- confirmation for destructive actions

Use a clean professional interface.

Do not over-design it.

STOP after completing Stage 8.

---

# STAGE 9: UI POLISH

Goal:

Make the application portfolio-ready.

Add:

- responsive design
- mobile layout
- dark mode
- consistent spacing
- reusable components
- clear typography
- buttons
- forms
- alerts
- loading indicators
- empty states
- error states

Add charts using Recharts or Chart.js.

Do not spend excessive time on visual perfection.

The goal is:

clean + professional + functional

not:

Dribbble-level design.

STOP after completing Stage 9.

---

# STAGE 10: AI FOUNDATION

Goal:

Add AI without coupling the application to one provider.

Create:

backend/app/services/ai_client.py

Environment variables:

AI_PROVIDER=gemini
AI_API_KEY=

Implement the Gemini provider using the current supported Gemini API/SDK.

Keep the abstraction designed so OpenAI or Anthropic can be added later without changing the API layer.

Never call the AI provider directly from React.

All AI calls must go through FastAPI.

Implement:

- timeout handling
- API failure handling
- structured JSON parsing
- validation of AI responses
- useful error messages

Do not allow malformed AI responses to crash the application.

Do not hard-code the API key.

STOP after completing Stage 10.

---

# STAGE 11: AI RESUME ANALYSIS

Create:

POST /api/v1/ai/resume-analysis

Input:

- resume text
- job description

Return structured information such as:

match_score
matching_skills
missing_skills
strengths
weaknesses
recommendations

Use structured output.

Validate the response server-side.

The frontend should display the result clearly.

Do not make unsupported claims about the user's qualifications.

STOP after completing Stage 11.

---

# STAGE 12: AI JOB DESCRIPTION MATCH

Create:

POST /api/v1/ai/jd-match

Compare:

- resume
- job description

Return:

- matched keywords
- missing keywords
- relevant skills
- important requirements
- match score

Handle AI failures gracefully.

STOP after completing Stage 12.

---

# STAGE 13: AI COVER LETTER

Create:

POST /api/v1/ai/cover-letter

Input:

- resume
- job description
- company
- role

Return:

- cover letter draft

The UI should allow the user to copy the result.

Do not pretend the AI-generated letter is guaranteed to be factually accurate.

STOP after completing Stage 13.

---

# STAGE 14: AI RATE LIMITING AND COST CONTROL

Before deployment, protect AI endpoints.

Implement a simple per-user rate limit.

Do not introduce Redis unless genuinely necessary.

For the MVP, an in-memory solution is acceptable if its limitations are documented.

Also:

- limit input size
- set request timeout
- handle provider errors
- avoid unnecessary duplicate AI requests

Document the design in DECISIONS.md.

STOP after completing Stage 14.

---

# STAGE 15: TESTING AND SECURITY REVIEW

Perform a complete review.

Check:

### Authentication

- password hashing
- token expiration
- refresh flow
- invalid tokens
- unauthorized requests

### Authorization

Confirm users cannot:

- read another user's applications
- modify another user's applications
- delete another user's applications
- access another user's interviews

### API

Check:

- validation
- 404s
- 401s
- 422s
- malformed requests
- empty data

### AI

Check:

- API key isn't exposed
- frontend never calls provider directly
- timeout handling
- malformed AI responses
- rate limiting

### Frontend

Check:

- loading states
- error states
- authentication redirects
- API failures
- mobile layout

Run the complete test suite.

Fix actual problems found.

Do not create unnecessary complexity merely to make the checklist longer.

STOP after completing Stage 15.

---

# STAGE 16: DEPLOYMENT

Goal:

Deploy the working application.

## PostgreSQL

Use Neon free PostgreSQL.

Configure:

DATABASE_URL

Run Alembic migrations against production.

Never commit credentials.

## Backend

Deploy FastAPI to Render free web service.

Configure:

- build command
- start command
- environment variables
- CORS
- production configuration

Ensure:

GET /health

works in production.

Remember that the Render free service can spin down after inactivity.

Do not design the application around a paid uptime solution.

## Frontend

Deploy React/Vite frontend to Vercel.

Configure:

VITE_API_BASE_URL

to point to the deployed backend.

Configure production CORS correctly.

STOP after completing Stage 16.

---

# STAGE 17: PRODUCTION VERIFICATION

Test the actual deployed application.

Verify:

1. Frontend loads.
2. Signup works.
3. Login works.
4. Logout works.
5. Applications can be created.
6. Applications can be edited.
7. Applications can be deleted.
8. Search works.
9. Filters work.
10. Interview rounds work.
11. Dashboard analytics work.
12. AI resume analysis works.
13. AI JD matching works.
14. Cover-letter generation works.
15. CORS works.
16. Mobile layout works.
17. Refreshing pages does not break routing.
18. Backend health endpoint works.

If something fails:

1. Diagnose it.
2. Fix it.
3. Retest it.
4. Do not simply tell me that it failed.

STOP after completing Stage 17.

---

# STAGE 18: PORTFOLIO PREPARATION

Prepare the project for GitHub and job applications.

Create a strong README containing:

- project overview
- problem solved
- features
- architecture
- tech stack
- database design
- API overview
- AI architecture
- local setup
- environment variables
- deployment architecture
- screenshots
- known limitations
- future improvements

Create a concise architecture diagram in the README.

Explain:

React
  ↓
FastAPI
  ↓
SQLAlchemy
  ↓
PostgreSQL

and:

React
  ↓
FastAPI AI endpoint
  ↓
AI abstraction
  ↓
Gemini

Do not exaggerate project capabilities.

STOP after completing Stage 18.

---

# 5. IMPORTANT IMPLEMENTATION RULES

## Keep the MVP small

Do NOT add:

- social login
- notifications
- email systems
- browser extensions
- job scraping
- complex background workers
- Redis
- Kubernetes
- microservices
- payment systems
- recommendation engines
- complicated DevOps infrastructure

unless explicitly requested later.

---

# 6. TIME AND BURNOUT RULE

This project is intentionally designed to be completed incrementally.

Do not create unnecessary work.

For every stage, prioritize:

1. Working functionality
2. Correct architecture
3. Tests
4. Reasonable UI
5. Documentation
6. Polish

Do not spend hours perfecting minor visual details while core functionality is unfinished.

If something is taking disproportionately long, choose the simplest reasonable implementation and document the tradeoff.

The target is a working portfolio project, not a commercial SaaS product.

---

# 7. AI AGENT BEHAVIOR

When working on this project:

- Do not blindly rewrite files.
- Inspect existing code first.
- Reuse existing components and utilities.
- Keep functions reasonably small.
- Keep modules focused.
- Avoid duplicate logic.
- Do not install packages without a reason.
- Explain why a new dependency is necessary.
- Do not expose secrets.
- Do not fabricate successful tests.
- Do not claim deployment succeeded unless it actually succeeded.
- Do not skip tests when tests are requested.
- Do not silently change the architecture.
- If you encounter a limitation, implement the simplest safe fallback and document it.

---

# 8. GIT WORKFLOW

After each meaningful completed stage:

1. Check git diff.
2. Review changed files.
3. Run relevant tests.
4. Create a clear commit.

Suggested commits:

feat: initialize project foundation
feat: add database models and migrations
feat: implement authentication
feat: add application CRUD
feat: add interview tracking
feat: add analytics API
feat: add frontend authentication
feat: build application dashboard
feat: polish responsive UI
feat: add AI provider abstraction
feat: add resume analysis
feat: add job description matching
feat: add cover letter generation
test: add security and integration coverage
chore: prepare production deployment
docs: prepare portfolio documentation

Do not make one enormous commit containing the entire project.

---

# 9. DEFINITION OF DONE

The project is finished only when:

- backend works locally
- frontend works locally
- PostgreSQL works
- migrations work
- authentication works
- CRUD works
- ownership/security works
- interviews work
- analytics work
- frontend is responsive
- AI features work
- AI keys are protected
- tests pass
- backend is deployed
- frontend is deployed
- production database is connected
- production authentication works
- production CRUD works
- production AI features work
- README is complete
- .env.example files exist
- no real secrets are committed

---

# 10. FIRST INSTRUCTION

You are currently starting from a fresh repository.

ONLY perform STAGE 1.

Do not implement future stages.

First inspect the repository.

Then create the project foundation.

Run the necessary checks.

At the end, report:

STAGE 1 COMPLETE

Implemented:
- ...

Files created/modified:
- ...

Commands/tests:
- ...

Manual verification:
- ...

Next stage:
STAGE 2

Then STOP.