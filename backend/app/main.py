# -----------------------------------------------------------------------------
#  FCC-Physics-Event : API Version 1
#
#  Copyright (c) 2026 CERN — Apache License 2.0
#  Developer: Kid A  |  amir.ebh@cern.ch
# -----------------------------------------------------------------------------

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

# ------------------------------------------------------------------
# Internal imports
# ------------------------------------------------------------------

from app.middleware import build_cors_middleware
from app.middleware import LoggingMiddleware
from app.middleware import TimingMiddleware

from app.routers import auth_router
from app.routers import entities_router as entities_router
from app.routers import navigation_router as navigation_router

from backend.app.workers.file_watcher import FileWatcherService
from app.storage.database import Database

from app.utils.auth_utils import AUTH_ENABLED, load_cern_endpoints
from app.utils.config_utils import get_config
from app.utils.gclql_query_parser_utils import QueryParser
from app.utils.logging_utils import get_logger, setup_logging

from app.api.v1.apiV1 import ApiV1

# ------------------------------------------------------------------
# Globals
# ------------------------------------------------------------------

logger = get_logger(__name__)
config = get_config()

database = Database()
query_parser = QueryParser(database=database)
file_watcher = FileWatcherService(database=database)

# ------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ------------------------------------------------------------------

@asynccontextmanager
async def lifespan(_: FastAPI) -> Any:
    """Handles application startup and shutdown entities."""
    setup_logging()

    # --- Startup ---
    await database.setup(config)

    if AUTH_ENABLED:
        logger.info("Authentication is enabled, loading CERN endpoints...")
        await load_cern_endpoints()
    else:
        logger.info("Authentication is disabled, skipping CERN endpoint loading")

    await query_parser.setup()
    await file_watcher.start()

    yield

    # --- Shutdown ---
    await file_watcher.stop()
    await database.aclose()

# ------------------------------------------------------------------
# App initialization
# ------------------------------------------------------------------

app = FastAPI(
    title="Universal Metadata Browser API",
    description="API for querying and managing metadata entities.",
    lifespan=lifespan,
)

# ------------------------------------------------------------------
# Middleware stack (ORDER MATTERS)
#
# Request flow:
#   CORS → Session → Logging → Timing → route
#
# Response flow:
#   route → Timing → Logging → Session → CORS
# ------------------------------------------------------------------

# 1. CORS (outermost — handles preflight early)
build_cors_middleware(app)

# 2. Session middleware (only if auth is enabled)
if AUTH_ENABLED:
    secret_key = config.get("general.application_secret_key")

    if not secret_key:
        logger.warning(
            "Auth is enabled but no secret key provided - session middleware disabled"
        )
    else:
        app.add_middleware(
            SessionMiddleware,
            secret_key=secret_key,
            https_only=config.get("general.https_only").lower() == "true",
            same_site="lax",
            max_age=3600,
            session_cookie=config.get(
                "general.cookie_prefix", "universal-metadata-browser"
            ),
            domain=None,
        )
        logger.info("Session middleware enabled")
else:
    logger.info("Session middleware disabled - auth is disabled")

# 3. Logging
app.add_middleware(LoggingMiddleware)

# 4. Timing (innermost — closest to route handler)
app.add_middleware(TimingMiddleware)

# ------------------------------------------------------------------
# Global exception handler
# ------------------------------------------------------------------

@app.exception_handler(Exception)
async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch all unhandled exceptions and return a standardized 500 response."""
    logger.error(
        f"Unhandled exception for {request.method} {request.url}",
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "An internal server error occurred. Please try again later.",
            "status": 500,
            "details": {
                "error": "internal_error",
                "message": f"Unhandled exception: {str(exc)}",
            },
        },
    )

# ------------------------------------------------------------------
# Router dependency initialization
# ------------------------------------------------------------------

auth_router.init_dependencies(database)
entities_router.init_dependencies(database, query_parser)
navigation_router.init_dependencies(database)

# ------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------

app.include_router(auth_router.router)
app.include_router(entities_router.router)
app.include_router(navigation_router.router)
app.include_router(ApiV1().router)
