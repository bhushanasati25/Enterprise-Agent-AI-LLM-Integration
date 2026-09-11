"""
Enterprise Agent AI — Security Module

API key validation, JWT utilities, and rate limiting middleware.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def validate_api_key(
    api_key: str | None = Security(api_key_header),
) -> str:
    """
    Validate the API key from request headers.
    In development mode, accepts any non-empty key or skips validation.
    """
    settings = get_settings()

    if settings.environment in ("development", "testing"):
        return api_key or "dev-key"

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    # In production, validate against stored keys
    # For now, accept the configured JWT secret as a valid API key
    if api_key != settings.jwt_secret_key:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return api_key


def create_access_token(data: dict[str, Any], expires_minutes: int = 60) -> str:
    """Create a JWT access token."""
    settings = get_settings()
    to_encode = data.copy()
    to_encode["exp"] = time.time() + (expires_minutes * 60)
    to_encode["iat"] = time.time()
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token-bucket rate limiting middleware.
    Limits requests per client IP per minute.
    """

    def __init__(self, app, requests_per_minute: int = 100, burst: int = 20):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self._buckets: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"tokens": burst, "last_refill": time.time()}
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/ready", "/metrics"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        bucket = self._buckets[client_ip]

        # Refill tokens
        now = time.time()
        elapsed = now - bucket["last_refill"]
        refill = elapsed * (self.requests_per_minute / 60.0)
        bucket["tokens"] = min(self.burst, bucket["tokens"] + refill)
        bucket["last_refill"] = now

        # Check if request is allowed
        if bucket["tokens"] < 1:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after_seconds": int(60 / self.requests_per_minute),
                },
                headers={"Retry-After": str(int(60 / self.requests_per_minute))},
            )

        bucket["tokens"] -= 1
        return await call_next(request)
