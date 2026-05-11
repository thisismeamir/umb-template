# -----------------------------------------------------------------------------
#  FCC-Physics-Event : API Version 1
#
#  Copyright (c) 2026 CERN
#
#  This file is part of the FCC-Physics-Event project and is licensed under
#  the Apache License, Version 2.0.
#  You may obtain a copy of the License at:
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Developer: Kid A
#  Contact:   amir.ebh@cern.ch  |  thisismeamir@outlook.com
#  GitHub:    https://github.com/thisismeamir
# -----------------------------------------------------------------------------
"""
LoggingMiddleware

Emits one structured log entry per request containing:
  - correlation_id : either forwarded from X-Correlation-ID header or freshly
                     generated, and echoed back on the response so clients can
                     trace a request end-to-end across services
  - method / path / status
  - duration_ms
  - client IP (respects X-Forwarded-For for requests behind the CERN nginx proxy)

Log level:
  - 4xx responses  → WARNING  (client error, worth noticing but not alerting)
  - 5xx responses  → ERROR    (server fault, should alert)
  - everything else → INFO

The correlation ID is attached to the response as X-Correlation-ID so it
appears in browser devtools and can be cross-referenced with server logs.

Registration in main.py:
    app.add_middleware(LoggingMiddleware)
"""
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.utils.logging import get_logger

logger = get_logger(__name__)

# Paths that generate noise without value — skip logging them.
_SILENT_PATHS: frozenset[str] = frozenset({
    "/v1/health",
    "/metrics",
    "/favicon.ico",
})


class LoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in _SILENT_PATHS:
            return await call_next(request)

        correlation_id = (
            request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        )
        client_ip = _resolve_client_ip(request)
        start     = time.perf_counter()

        response  = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        status      = response.status_code

        _log(
            status       = status,
            method       = request.method,
            path         = request.url.path,
            duration_ms  = duration_ms,
            correlation_id = correlation_id,
            client_ip    = client_ip,
        )

        response.headers["X-Correlation-ID"] = correlation_id
        return response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_client_ip(request: Request) -> str:
    """
    Prefer X-Forwarded-For (set by the CERN nginx reverse proxy).
    Falls back to the direct connection address.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _log(
    status: int,
    method: str,
    path: str,
    duration_ms: float,
    correlation_id: str,
    client_ip: str,
) -> None:
    payload = {
        "correlation_id" : correlation_id,
        "method"         : method,
        "path"           : path,
        "status"         : status,
        "duration_ms"    : round(duration_ms, 3),
        "client_ip"      : client_ip,
    }

    if status >= 500:
        logger.error("request failed",   extra=payload)
    elif status >= 400:
        logger.warning("client error",   extra=payload)
    else:
        logger.info("request completed", extra=payload)