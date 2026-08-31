"""Per-user AI rate limiting backed by Redis.

PostgreSQL remains the source of truth. Redis stores only ephemeral counters.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from typing import Protocol

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

RATE_LIMIT_KEY_PREFIX = "ratelimit:ai"
AI_RATE_LIMIT_DETAIL = "AI request limit exceeded. Please try again later."

# Atomic INCR + EXPIRE so concurrent requests cannot skip the TTL on a new key.
_INCR_EXPIRE_SCRIPT = """
local current = redis.call("INCR", KEYS[1])
if current == 1 then
  redis.call("EXPIRE", KEYS[1], tonumber(ARGV[1]))
end
return current
"""


class RateLimitBackend(Protocol):
    async def incr_with_expire(self, key: str, ttl_seconds: int) -> int: ...

    async def aclose(self) -> None: ...


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int
    key: str
    count: int


def rate_limit_key(user_id: int, window_id: int) -> str:
    """Namespaced counter: ratelimit:ai:{user_id}:{window}. Stores no PII."""
    return f"{RATE_LIMIT_KEY_PREFIX}:{user_id}:{window_id}"


def window_id_and_ttl(now: float, window_seconds: int) -> tuple[int, int]:
    """Fixed-window id and remaining TTL (seconds, at least 1)."""
    window_id = int(now // window_seconds)
    remaining = window_seconds - (now % window_seconds)
    ttl = max(1, math.ceil(remaining))
    return window_id, ttl


class RedisRateLimitBackend:
    """Thin Redis wrapper. The URL is never logged or included in errors."""

    def __init__(self, url: str) -> None:
        self._url = url
        self._client: Redis | None = None

    def _client_from_url(self) -> Redis:
        if not self._url.strip():
            raise ConnectionError("Redis is not configured")
        try:
            return Redis.from_url(
                self._url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
        except (ValueError, RedisError, OSError, TimeoutError) as exc:
            raise ConnectionError("Redis is not configured") from exc

    def _get_client(self) -> Redis:
        if self._client is None:
            self._client = self._client_from_url()
        return self._client

    async def incr_with_expire(self, key: str, ttl_seconds: int) -> int:
        client = self._get_client()
        result = await client.eval(_INCR_EXPIRE_SCRIPT, 1, key, str(ttl_seconds))
        return int(result)

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


class AIRateLimiter:
    def __init__(
        self,
        backend: RateLimitBackend,
        *,
        max_requests: int,
        window_seconds: int,
    ) -> None:
        self._backend = backend
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def hit(self, user_id: int, *, now: float | None = None) -> RateLimitDecision:
        moment = time.time() if now is None else now
        window_id, ttl = window_id_and_ttl(moment, self.window_seconds)
        key = rate_limit_key(user_id, window_id)
        try:
            count = await self._backend.incr_with_expire(key, ttl)
        except (RedisError, OSError, TimeoutError, ConnectionError):
            logger.warning(
                "AI rate limiter: Redis unavailable; allowing request (fail-open)"
            )
            return RateLimitDecision(
                allowed=True,
                retry_after_seconds=0,
                key=key,
                count=0,
            )
        if count > self.max_requests:
            return RateLimitDecision(
                allowed=False,
                retry_after_seconds=ttl,
                key=key,
                count=count,
            )
        return RateLimitDecision(
            allowed=True,
            retry_after_seconds=0,
            key=key,
            count=count,
        )

    async def aclose(self) -> None:
        await self._backend.aclose()


_limiter: AIRateLimiter | None = None


def build_ai_rate_limiter(settings: Settings | None = None) -> AIRateLimiter:
    cfg = settings or get_settings()
    return AIRateLimiter(
        RedisRateLimitBackend(cfg.redis_url),
        max_requests=cfg.ai_rate_limit_requests,
        window_seconds=cfg.ai_rate_limit_window_seconds,
    )


def get_ai_rate_limiter() -> AIRateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = build_ai_rate_limiter()
    return _limiter


async def close_ai_rate_limiter() -> None:
    global _limiter
    if _limiter is not None:
        await _limiter.aclose()
        _limiter = None
