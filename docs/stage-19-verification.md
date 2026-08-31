# Stage 19 production verification results

Last updated: 2026-08-31.

This file records **actual** verification. It does not treat a successful local pytest run as a live AWS deployment.

## AWS resources used

None confirmed from this environment.

| Resource | Status |
| --- | --- |
| Region | Target remains `ap-south-1` (documented in Stage 18). Not queried: AWS CLI is not installed on the developer machine used for this check. |
| EC2 instance | Not found. No public ApplyLens origin was provided, and no SSH private key is present under `%USERPROFILE%\.ssh`. |
| Elastic IP | Not confirmed. |
| Security group | Not confirmed. Intended rules remain: SSH from your IP, 80 and 8000 from the internet; never 5432, 6379, or Docker. |
| RDS / ElastiCache / ECS / EKS / ALB | Not used (by design). |

An unrelated host in `known_hosts` (`3.73.74.86`) was probed: TCP 80, 8000, 5432, and 6379 all timed out. It is not a verified ApplyLens deployment.

## Repository verification (performed)

| Check | Result |
| --- | --- |
| Production Compose publishes only 80 and 8000 | Pass (`docker-compose.prod.yml`; pytest `test_production_compose.py`) |
| Postgres and Redis unpublished | Pass (no host `ports:` for those services) |
| `ENVIRONMENT=production` JWT rules | Pass (`test_settings.py`: default and short secrets rejected) |
| `.env.production.example` is not the dev JWT default | Pass |
| Secrets not in git | `.env`, `*.pem`, `.env.production` remain gitignored; example files use placeholders |
| GitHub Actions CI on `main` | Last observed run succeeded (2026-08-31, “Prepare ApplyLens for AWS EC2 Docker Compose deployment”) |
| Docker / local Compose on this agent | Not re-run: Docker CLI was not available in the Stage 19 shell |

## Live EC2 verification (not performed)

| Check | Result |
| --- | --- |
| Compose up / healthchecks / Alembic | Not run (no SSH session) |
| `GET /health` on public IP | Not run |
| Frontend load, signup, login, logout | Not run |
| Application CRUD, search, filters | Not run |
| Interview rounds | Not run |
| Dashboard analytics | Not run |
| CORS from `http://<public-ip>` | Not run |
| SPA refresh (`/applications`) | Not run |
| Mobile layout | Not run (needs a browser against the live origin) |
| AI resume analysis / JD match / cover letter | Not run (no host; `--live-ai` unused) |
| Redis PING and `ratelimit:ai:*` | Not run |
| Postgres/Redis closed on the internet | Not run against a real ApplyLens IP |
| Container restart | Not run |

Stage 19 is **not complete**.

## How to finish Stage 19

1. Complete the manual AWS console steps in `docs/aws-ec2-deployment.md` (Ubuntu `t3.micro` in `ap-south-1`, security group, optional Elastic IP).
2. On the instance: install Docker, clone the repo, copy `.env.production.example` to `.env`, set real `JWT_SECRET`, `POSTGRES_PASSWORD`, `VITE_API_BASE_URL`, `CORS_ORIGINS`, and optional `AI_API_KEY`.
3. `docker compose --env-file .env -f docker-compose.prod.yml up -d --build`
4. On the host: `bash scripts/ec2_host_verify.sh`
5. From a laptop: `python scripts/verify_production.py --host YOUR_EC2_PUBLIC_IP` and add `--live-ai` only if Gemini is configured.
6. Open `http://YOUR_EC2_PUBLIC_IP` in a browser (including a narrow viewport) and confirm login, logout, and a page refresh on `/applications`.
7. Update this file with the public IP (not the key, not `.env`) and the command output summaries.

Do not commit `.env`, PEM files, AWS access keys, or `AI_API_KEY`.
