"""
Rate limiting middleware for the Observatorio API.
In-memory sliding window per IP. Resets on cold start (acceptable for Vercel).
"""
import time
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter per client IP.

    Args:
        app: The ASGI app.
        requests_per_minute: Max requests allowed per IP per minute.
        burst_per_second: Max requests allowed per IP per second (burst protection).
    """

    def __init__(self, app, requests_per_minute: int = 60, burst_per_second: int = 10):
        super().__init__(app)
        self.rpm = requests_per_minute
        self.bps = burst_per_second
        self._minute_windows: dict[str, list[float]] = defaultdict(list)
        self._second_windows: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _clean_window(self, timestamps: list[float], window_seconds: float, now: float) -> list[float]:
        cutoff = now - window_seconds
        return [t for t in timestamps if t > cutoff]

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for docs and health check
        path = request.url.path
        if path in ("/", "/docs", "/redoc", "/openapi.json") or request.method == "OPTIONS":
            return await call_next(request)

        now = time.time()
        ip = self._get_client_ip(request)

        # Per-minute check
        self._minute_windows[ip] = self._clean_window(self._minute_windows[ip], 60.0, now)
        if len(self._minute_windows[ip]) >= self.rpm:
            retry_after = int(60 - (now - self._minute_windows[ip][0])) + 1
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Demasiadas solicitudes. Intente de nuevo más tarde.",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        # Per-second burst check
        self._second_windows[ip] = self._clean_window(self._second_windows[ip], 1.0, now)
        if len(self._second_windows[ip]) >= self.bps:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Demasiadas solicitudes por segundo. Reduzca la velocidad.",
                    "retry_after_seconds": 1,
                },
                headers={"Retry-After": "1"},
            )

        # Record the request
        self._minute_windows[ip].append(now)
        self._second_windows[ip].append(now)

        # Periodic cleanup: remove IPs with no recent activity (every ~100 requests)
        if sum(len(v) for v in self._minute_windows.values()) % 100 == 0:
            stale = [k for k, v in self._minute_windows.items() if not v]
            for k in stale:
                del self._minute_windows[k]
                self._second_windows.pop(k, None)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rpm)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.rpm - len(self._minute_windows[ip]))
        )
        return response
