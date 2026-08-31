#!/usr/bin/env bash
# Run on the Ubuntu EC2 host from the cloned applylens directory.
# Does not print secrets. Does not exhaust the AI quota.
set -euo pipefail

COMPOSE=(docker compose --env-file .env -f docker-compose.prod.yml)

echo "== compose ps =="
"${COMPOSE[@]}" ps

echo "== health from localhost =="
curl -sS http://127.0.0.1:8000/health
echo
curl -sS -o /dev/null -w "frontend_http=%{http_code}\n" http://127.0.0.1/

echo "== jwt / environment (values not printed) =="
"${COMPOSE[@]}" exec -T backend python -c "
from app.core.config import DEV_JWT_SECRET, settings
assert settings.environment.lower() == 'production'
assert settings.debug is False
secret = settings.jwt_secret.strip()
assert secret != DEV_JWT_SECRET
assert len(secret) >= 32
print('production_jwt_ok')
print('redis_configured', bool(settings.redis_url))
print('ai_key_configured', bool(settings.ai_api_key_value))
"

echo "== postgres ready (compose network) =="
"${COMPOSE[@]}" exec -T postgres pg_isready

echo "== redis ping (compose network) =="
"${COMPOSE[@]}" exec -T redis redis-cli PING

echo "== host listeners (5432/6379 should not be public) =="
ss -lnt | grep -E ':80|:8000|:5432|:6379|:2375|:2376' || true

echo "== backend recent logs (migrations / redis) =="
"${COMPOSE[@]}" logs --tail=80 backend

echo "== redis rate-limit keys after any AI traffic =="
"${COMPOSE[@]}" exec -T redis redis-cli KEYS 'ratelimit:ai:*' || true

echo "== restart backend and re-check health =="
"${COMPOSE[@]}" restart backend
sleep 20
"${COMPOSE[@]}" ps
curl -sS http://127.0.0.1:8000/health
echo

echo "Host verification commands finished. Do not paste .env or JWT_SECRET into chat."
