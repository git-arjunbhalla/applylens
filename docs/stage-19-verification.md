# Stage 19 production verification results

Last updated: 2026-08-31 (Stage 20 confirmation of the same host).

This file records **actual** verification. A successful local pytest run is not a live AWS deployment.

## AWS resources used

| Resource | Status |
| --- | --- |
| Region | `ap-south-1` |
| EC2 public IPv4 | `13.203.208.130` |
| Frontend origin | `http://13.203.208.130` |
| API origin | `http://13.203.208.130:8000` |
| Elastic IP | Not asserted in this repository (the address above is the verified public IP). |
| Security group (intended) | SSH from operator IP; 80 and 8000 from the internet; never 5432, 6379, or Docker. |
| RDS / ElastiCache / ECS / EKS / ALB | Not used (by design). |

## Repository verification

| Check | Result |
| --- | --- |
| Production Compose publishes only 80 and 8000 | Pass (`docker-compose.prod.yml`; pytest `test_production_compose.py`) |
| Postgres and Redis unpublished | Pass (no host `ports:` for those services) |
| `ENVIRONMENT=production` JWT rules | Pass (`test_settings.py`) |
| `.env.production.example` is not the dev JWT default | Pass |
| Secrets not in git | `.env`, `*.pem`, `.env.production` remain gitignored; example files use placeholders |

## Live EC2 verification (recorded)

Operator report for Stage 19 (2026-08-31), on this public IP:

| Check | Result |
| --- | --- |
| Frontend from a Windows browser | Pass |
| Backend `GET /health` | Pass |
| Postgres healthy (Compose, not public) | Pass |
| Redis healthy (Compose, not public) | Pass |
| Production smoke tests | Pass |

Stage 20 re-checked from the developer machine (2026-08-31): `python scripts/verify_production.py --host 13.203.208.130` passed (AI smokes skipped without `--live-ai`). Guest login/signup screenshots were captured from that origin. New nginx headers and `no-new-privileges` apply after production images are rebuilt on the host.

Do not commit `.env`, PEM files, AWS access keys, or `AI_API_KEY`.
