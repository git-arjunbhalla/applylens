# AWS EC2 deployment (Stages 18–19)

This document describes how to run ApplyLens on a single EC2 instance using the existing Docker Compose architecture. Console launch, key pair, security group, and Elastic IP remain **manual**. Stage 19 live verification for public IP `13.203.208.130` is recorded in [`docs/stage-19-verification.md`](stage-19-verification.md).

Region: **ap-south-1** (Mumbai).

## Architecture

```
Internet
  |
  |  TCP 80 (frontend), TCP 8000 (API)
  v
EC2 (Ubuntu)  —  Docker Compose
  +-- frontend   React production build served by nginx   :80
  +-- backend    FastAPI + Alembic on start               :8000
  +-- postgres   source of truth                          Compose DNS only
  +-- redis      ephemeral AI rate-limit counters         Compose DNS only
```

PostgreSQL and Redis stay on the Compose private network (`postgres`, `redis`). They are not published on the host and must not be opened in the security group.

The browser calls FastAPI at `VITE_API_BASE_URL` (baked into the frontend image at build time). That is a public API origin, not a secret. `AI_API_KEY`, `JWT_SECRET`, `DATABASE_URL`, and `REDIS_URL` are backend-only.

Local development still uses `docker-compose.yml`. Production on EC2 uses `docker-compose.prod.yml`.

## Recommended EC2 configuration

Choose values that stay within the current AWS Free Tier or account credits. Free-tier instance types depend on when the AWS account was created.

| Setting | Recommendation |
| --- | --- |
| Region | `ap-south-1` |
| AMI | Ubuntu Server 24.04 LTS, **x86_64**, Canonical. Pick the current AMI in the EC2 launch wizard; do not hard-code an AMI ID. |
| Architecture | **x86_64**. Official images used here (Python, Node, nginx, Postgres, Redis) also publish arm64, but Stage 18 verification builds on amd64 (local Windows and GitHub Actions `ubuntu-latest`). |
| Instance type | `t3.micro` (1 vCPU, 1 GiB). Newer accounts may also use `t3.small` if credits allow more memory for image builds. |
| Storage | 20–30 GiB **gp3** root volume |
| Key pair | Create in `ap-south-1`. Download the `.pem` once. Store it outside the repo. |
| Public IP | Prefer an **Elastic IP** associated with the instance so `VITE_API_BASE_URL` and CORS do not need a rebuild after stop/start. |

ARM64 (`t4g.micro`) is optional only if you **build images on that instance**. Do not run amd64 images on Graviton without emulation.

`t3.micro` has 1 GiB RAM. Enable a 2 GiB swap file before `docker compose build` so the frontend Node build is less likely to be killed.

## Security group (least privilege)

Create a security group in `ap-south-1`. Inbound:

| Port | Protocol | Source | Purpose |
| --- | --- | --- | --- |
| 22 | TCP | Your public IPv4 `/32` only | SSH |
| 80 | TCP | `0.0.0.0/0` (and `::/0` if IPv6 is used) | nginx frontend |
| 8000 | TCP | `0.0.0.0/0` (and `::/0` if IPv6 is used) | FastAPI (browser calls this origin) |

Do **not** open:

- 5432 (PostgreSQL)
- 6379 (Redis)
- 2375 / 2376 (Docker daemon)
- 8080 unless you intentionally run the local Compose file

Outbound: default allow-all so the instance can pull images, clone GitHub, and call Gemini.

Attach this security group to the instance. Restrict SSH to your IP and update the rule when your IP changes.

This deployment uses HTTP, not TLS. There is no Application Load Balancer, ACM certificate, or CloudFront distribution.

## MANUAL STEPS REQUIRED (AWS console)

1. Sign in to the AWS Management Console. Set the region to **ap-south-1**.
2. Create a key pair. Save the private key outside the repository.
3. Create the security group above.
4. Launch Ubuntu Server 24.04 LTS (`x86_64`), `t3.micro`, 20–30 GiB gp3, the key pair, and the security group. Allow a public IPv4 address.
5. (Recommended) Allocate an Elastic IP in `ap-south-1` and associate it with the instance.
6. Note the public IPv4 address. You will put it in `.env` as `VITE_API_BASE_URL` and `CORS_ORIGINS`.
7. Open SSH from your machine using the key pair. The remaining steps run on the instance.

Do not paste AWS access keys into this repository or into Docker Compose files.

## Commands on the EC2 host

Replace `YOUR_KEY.pem`, `YOUR_EC2_PUBLIC_IP`, and the GitHub clone URL.

### 1. SSH

```bash
ssh -i /path/to/YOUR_KEY.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### 2–3. Install Docker Engine and the Compose plugin

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker ubuntu
```

Log out and SSH back in so the `docker` group applies. Confirm:

```bash
docker version
docker compose version
```

Optional swap on `t3.micro`:

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

To persist swap across reboot, add `/swapfile none swap sw 0 0` to `/etc/fstab`.

### 4. Clone the repository

```bash
git clone https://github.com/YOUR_GITHUB_USER/applylens.git
cd applylens
```

### 5. Configure production environment

```bash
cp .env.production.example .env
nano .env
```

Set at least:

- `POSTGRES_PASSWORD` — long random value; URL-encode it if you later embed it in a hand-written `DATABASE_URL` (Compose interpolates it into `DATABASE_URL` for you)
- `JWT_SECRET` — unique, at least 32 characters; not the local development default
- `VITE_API_BASE_URL` — `http://YOUR_EC2_PUBLIC_IP:8000` (or Elastic IP)
- `CORS_ORIGINS` — `http://YOUR_EC2_PUBLIC_IP` (frontend on port 80; no `:80` suffix)
- `AI_API_KEY` — Gemini key on the host if you want live AI; leave empty otherwise

`.env` is gitignored. Do not copy it into images. Do not put backend secrets in `VITE_*` variables.

If the public address changes, update `.env` and rebuild the **frontend** image so the baked API origin matches.

### 6–7. Build and start

```bash
docker compose --env-file .env -f docker-compose.prod.yml build
docker compose --env-file .env -f docker-compose.prod.yml up -d
```

The backend entrypoint runs `alembic upgrade head` before uvicorn. A normal `up` reuses the `postgres_data` named volume and does not wipe existing rows.

### 8. Health checks

```bash
docker compose --env-file .env -f docker-compose.prod.yml ps
curl -sS http://127.0.0.1:8000/health
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1/
```

From your laptop (after security-group ports are open):

```bash
curl -sS http://YOUR_EC2_PUBLIC_IP:8000/health
python scripts/verify_production.py --host YOUR_EC2_PUBLIC_IP
```

Add `--live-ai` only when `AI_API_KEY` is set on the host. That flag sends **three** Gemini requests (one per AI feature) and must not be used to force HTTP 429.

Expected API body: `{"status":"ok"}`. `/health` does not query PostgreSQL.

On the EC2 host, after Compose is up:

```bash
bash scripts/ec2_host_verify.sh
```

### 9. Logs

```bash
docker compose --env-file .env -f docker-compose.prod.yml logs -f
docker compose --env-file .env -f docker-compose.prod.yml logs -f backend
docker compose --env-file .env -f docker-compose.prod.yml logs --tail=100 frontend
```

JSON-file logs on the host rotate at 10 MB × 3 files per service. CloudWatch is not enabled. It can be added later if you need instance-level log retention; it is not required for this project.

### 10. Restart

Recreate containers without deleting the Postgres volume:

```bash
docker compose --env-file .env -f docker-compose.prod.yml up -d
```

Rebuild after a code pull or `.env` URL change:

```bash
git pull
docker compose --env-file .env -f docker-compose.prod.yml up -d --build
```

### 11. Stop

```bash
docker compose --env-file .env -f docker-compose.prod.yml stop
```

Remove containers and the Compose network but **keep** the Postgres volume:

```bash
docker compose --env-file .env -f docker-compose.prod.yml down
```

### 12. Clean up

Delete unused images:

```bash
docker image prune
```

Destroy application containers **and** PostgreSQL data:

```bash
docker compose --env-file .env -f docker-compose.prod.yml down -v
```

Terminating the EC2 instance destroys EBS data unless you snapshot the volume or keep a backup. Redis is ephemeral by design; rate-limit counters reset on Redis restart.

## Environment variables (production)

Backend-only (Compose injects these; they must never be `VITE_*` build args):

| Variable | Role |
| --- | --- |
| `DATABASE_URL` | Built as `postgresql+asyncpg://...@postgres:5432/...` |
| `REDIS_URL` | `redis://redis:6379/0` |
| `JWT_SECRET` | Signs access and refresh tokens |
| `AI_API_KEY` | Gemini; optional if you are not testing AI |
| `CORS_ORIGINS` | Exact frontend origin (`http://IP`) |

Public frontend build arg:

| Variable | Role |
| --- | --- |
| `VITE_API_BASE_URL` | `http://IP:8000` |

## Stage 19 verification

Repository checks (no AWS account required):

- `docker-compose.prod.yml` publishes only 80 and 8000. PostgreSQL and Redis have no `ports:` mappings.
- `ENVIRONMENT=production` rejects the development `JWT_SECRET` and secrets shorter than 32 characters (`backend/tests/test_settings.py`).
- GitHub Actions CI on `main` runs pytest, Vitest, the frontend production build, and Compose file validation. CI does not deploy.

Live checks (require a running EC2 host in ap-south-1):

| Check | How |
| --- | --- |
| Frontend / SPA refresh | `GET http://IP/` and `GET http://IP/applications` return the nginx `index.html` |
| Backend health | `GET http://IP:8000/health` → `{"status":"ok"}` |
| Auth, CRUD, interviews, analytics | `python scripts/verify_production.py --host IP` |
| CORS | Script sends `Origin: http://IP` on signup and an OPTIONS preflight |
| Postgres / Redis not public | TCP 5432 and 6379 must not accept connections from the internet |
| JWT in production | Host script asserts `ENVIRONMENT=production` and a unique ≥32-char secret **without printing it** |
| Redis limiter | Host script `PING`s Redis and lists `ratelimit:ai:*` after at most three AI calls |
| Containers / restart | Host script prints `compose ps`, backend logs (Alembic on start), restarts backend, re-checks health |

Do not open 5432, 6379, or the Docker socket to verify them. Confirm they are closed from your laptop and that they are unpublished in Compose.

Recorded results: [`docs/stage-19-verification.md`](stage-19-verification.md).

## AI (Gemini)

Production supports `AI_PROVIDER=gemini`. Automated CI must not set `APPLYLENS_LIVE_GEMINI` or a real `AI_API_KEY`. After a real deploy, one successful request per AI feature is enough for a manual check. Do not send 10+ AI requests to prove rate limiting on the live quota; Redis `INCR` on `ratelimit:ai:*` after those three calls is the production evidence. HTTP 429 is covered by the automated test suite.

## Cost considerations

- One `t3.micro` (or equivalent free-tier type) plus a small gp3 volume is the intended footprint.
- Elastic IPs are typically free while associated with a running instance; idle unassociated Elastic IPs can incur a charge.
- Data transfer, extra EBS snapshots, and leaving the instance running after credits expire will cost money.
- Gemini has its own free-tier/quota limits separate from AWS.
- This setup does not use RDS, ElastiCache, ECS, EKS, ALB, or CloudWatch Logs.

## Known limitations

- HTTP only; traffic is not encrypted.
- Port 8000 is public because the SPA calls FastAPI directly.
- Single instance; no autoscaling or multi-AZ database.
- PostgreSQL lives on the instance volume; stopping or terminating EC2 without a snapshot loses data.
- Redis counters reset when the Redis container is recreated.
- Changing the public IP requires a frontend image rebuild.
- `t3.micro` may need swap to finish `npm` image builds.
- Stage 18 prepares the repository. Stage 19 live results for this project are in `docs/stage-19-verification.md`. The demo uses HTTP, not TLS.
