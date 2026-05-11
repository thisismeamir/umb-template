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
TimingMiddleware

Measures wall-clock time from request received to response sent and injects
it as the X-Process-Time header (milliseconds, 3 decimal places).

Useful for:
  - Client-side performance monitoring
  - Identifying slow endpoints in logs without a full APM setup
  - Smoke-testing that a deploy didn't regress latency

Registration in main.py:
    app.add_middleware(TimingMiddleware)
"""
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TimingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time"] = f"{elapsed_ms:.3f}ms"
        return response