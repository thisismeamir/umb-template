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
CORS configuration.

Keeps CORS rules as explicit typed code rather than scattered kwargs in main.py.
Origins and policy are driven by the app config so they can differ between
development, staging, and production without touching application code.

CERN context:
  - Development: localhost frontends (port varies per developer)
  - Staging/Production: fcc-physics.web.cern.ch and related CERN web domains
  - The CERN SSO redirect flow requires credentials=True on authenticated routes

Registration in main.py:
    from app.api.middleware.cors import build_cors_middleware
    build_cors_middleware(app)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings


def build_cors_middleware(app: FastAPI) -> None:
    """
    Attaches CORSMiddleware to the app using values from config.

    Kept as a function rather than a class so the middleware attaches
    via the standard FastAPI path and plays nicely with the middleware
    stack order in main.py.
    """
    settings = get_settings()

    app.add_middleware(
        CORSMiddleware,
        allow_origins     = settings.cors_allowed_origins,
        allow_methods     = settings.cors_allowed_methods,
        allow_headers     = settings.cors_allowed_headers,
        allow_credentials = settings.cors_allow_credentials,
        max_age           = settings.cors_max_age,
    )