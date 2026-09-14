import hashlib
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse
from redis import Redis
from redis.exceptions import RedisError

from app.config import Settings
from app.errors import error_content


class RequestRateLimiter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True) if settings.environment == "production" else None
        self.local: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()

    def _client(self, request: Request) -> str:
        direct = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
        address = forwarded if direct in {"127.0.0.1", "::1"} and forwarded else direct
        secret = self.settings.operations_token.get_secret_value() if self.settings.operations_token else self.settings.database_password
        return hashlib.sha256(f"{secret}:{address}".encode()).hexdigest()

    def check(self, request: Request) -> tuple[bool, int, int]:
        limit = self.settings.auth_rate_limit_per_minute if request.url.path.startswith("/api/v1/auth/") else self.settings.api_rate_limit_per_minute
        key = f"akuru:rate:{self._client(request)}:{request.url.path}:{int(time.time() // 60)}"
        if self.redis:
            try:
                with self.redis.pipeline() as pipe:
                    pipe.incr(key); pipe.expire(key, 61); count, _ = pipe.execute()
            except RedisError:
                return False, 0, limit  # Production rate control fails closed.
            return int(count) <= limit, max(0, limit - int(count)), limit
        now = time.monotonic()
        with self.lock:
            bucket = self.local[key]
            while bucket and bucket[0] <= now - 60: bucket.popleft()
            bucket.append(now)
            return len(bucket) <= limit, max(0, limit - len(bucket)), limit

    def rejection(self) -> JSONResponse:
        return JSONResponse(status_code=429, content=error_content("rate_limited", "Too many requests. Try again shortly."), headers={"Retry-After": "60"})
