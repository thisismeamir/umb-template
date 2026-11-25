from __future__ import annotations

import logging
import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("umb.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs structured request method, path, status code, and latency in milliseconds."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        start_s = time.perf_counter()
        response: Response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start_s) * 1000.0
        request_id = getattr(request.state, "request_id", "-")
        logger.info(
            "http_request method=%s path=%s status=%d duration_ms=%.2f request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )
        return response
