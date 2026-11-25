from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TimingMiddleware(BaseHTTPMiddleware):
    """Injects X-Process-Time (ms) and X-Request-Id headers on every HTTP response."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        request_id = request.headers.get("X-Request-Id") or str(uuid4())
        request.state.request_id = request_id
        start_s = time.perf_counter()
        response: Response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start_s) * 1000.0
        response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"
        response.headers["X-Request-Id"] = request_id
        return response
