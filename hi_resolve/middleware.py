from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from hi_resolve.settings import settings

logger = logging.getLogger("hi_resolve")


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            ms,
        )
        response.headers["X-Process-Time-Ms"] = f"{ms:.1f}"
        return response


def setup_middleware(app: FastAPI) -> None:
    # Last added runs first — Timing wraps Session.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        same_site=settings.session_same_site,
        https_only=settings.session_https_only,
    )
    app.add_middleware(TimingMiddleware)
