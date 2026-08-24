# -----------------------------------------------------------------------------
#  UMB Template Backend
#  Copyright (c) 2026 CERN
#  Licensed under the Apache License, Version 2.0
# -----------------------------------------------------------------------------

from enum import Enum
from typing import Protocol, Dict, Iterable, Optional

import asyncpg
from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.params import Depends
from starlette.types import ASGIApp

from app.config import get_settings
from app.models.entity.EntityRoute import EntityRoute
from app.services.entity.EntityService import EntityService
from app.repositories.entry.EntryRepository import EntryRepository


# -----------------------------------------------------------------------------
# API Lifecycle
# -----------------------------------------------------------------------------
class ApiState(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"  # fully removed → 410


# -----------------------------------------------------------------------------
# Router Provider Contract
# -----------------------------------------------------------------------------
class RouterProvider(Protocol):
    @property
    def router(self) -> APIRouter: ...


# -----------------------------------------------------------------------------
# Internal Helpers
# -----------------------------------------------------------------------------
def _reject_sunset(version: str, latest: str):
    """
    Sunset is when the api is not only old but not even supported anymore.
    Encouraging the user to immediately change their api implementation.
    :param version:
    :param latest:
    :return: HTTPException
    """
    def _inner():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={
                "error": "deprecated_api_version",
                "message": f"{version} is no longer supported",
                "current_version": latest,
                "docs": f"/docs/{latest}",
            },
        )
    return _inner

def _deprecation_headers_middleware(version: str):
    """
    Deprecation would be a warning that this api is old.
    Although the api works they might need to change implementation later on.
    :param version:
    :return:
    """
    async def middleware(request: Request, call_next):
        response = await call_next(request)
        response.headers["Deprecation"] = "true"
        response.headers["Warning"] = f'299 - "API {version} is deprecated"'
        return response
    return middleware


# -----------------------------------------------------------------------------
# API Core
# -----------------------------------------------------------------------------

class Api:
    """
    Versioned API container with lifecycle-aware behavior.
    States:
        - ACTIVE: normal routing
        - DEPRECATED: still works, emits warnings
        - SUNSET: hard rejected with 410 Gone
    """

    def __init__(
        self,
        version: str,
        *,
        prefix: str = "/",
        state: ApiState = ApiState.ACTIVE,
        latest_version: str,
        dependencies: Optional[Iterable[Depends]] = None,
    ) -> None:

        self.version = version
        self.state = state
        self.latest_version = latest_version
        self.dependencies = list(dependencies or [])
        self._mounted = False

        # ---------------------------------------------------------------------
        # Router construction
        # ---------------------------------------------------------------------
        if self.state == ApiState.SUNSET:
            # All requests → 410
            self._router = APIRouter(
                prefix="",
                dependencies=[
                    Depends(_reject_sunset(self.version, self.latest_version))
                ],
                deprecated=True,
            )

        else:
            self._router = APIRouter(
                prefix="",
                dependencies=self.dependencies,
                deprecated=(self.state == ApiState.DEPRECATED),
            )

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    @property
    def router(self) -> APIRouter:
        return self._router

    def include(self, provider: RouterProvider) -> None:
        if self._mounted:
            raise RuntimeError("Cannot include routers after mounting")
        self._router.include_router(provider.router)

    def include_raw(
        self,
        router: APIRouter,
        *,
        prefix: str = "",
        tags: Optional[list[str]] = None,
    ) -> None:
        if self._mounted:
            raise RuntimeError("Cannot include routers after mounting")
        self._router.include_router(router, prefix=prefix, tags=tags)

    def mount(self, app: FastAPI) -> None:
        if self._mounted:
            raise RuntimeError("API already mounted")

        # Attach deprecation middleware if needed
        if self.state == ApiState.DEPRECATED:
            app.middleware("http")(
                _deprecation_headers_middleware(self.version)
            )

        app.include_router(self._router)
        self._mounted = True

    def as_subapp(self) -> ASGIApp:
        """
        Returns this API as an isolated sub-application.
        Strong isolation for deprecated/sunset versions.
        """
        sub = FastAPI(
            title=f"API {self.version}",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json"
        )

        if self.state == ApiState.SUNSET:
            @sub.middleware("http")
            async def reject_all(request: Request, call_next):
                return JSONResponse(
                    status_code=410,
                    content=self.gone(),
                )
        else:
            if self.state == ApiState.DEPRECATED:
                sub.middleware("http")(
                    _deprecation_headers_middleware(self.version)
                )
            sub.include_router(self._router)

        return sub

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------
    def gone(self) -> Dict[str, str]:
        return {
            "error": "deprecated_api_version",
            "message": f"{self.version} is no longer supported",
            "current_version": self.latest_version,
            "docs": f"/docs/{self.latest_version}",
        }



class Provider:

    @staticmethod
    async def _makeConn() -> asyncpg.Connection:
        settings = get_settings()
        return await asyncpg.connect(
            host=settings.databaseHost,
            port=settings.databasePort,
            user=settings.databaseUser,
            password=settings.databasePassword,
            database=settings.databaseDatabase
        )

    @staticmethod
    async def entryRepository() -> EntryRepository:
        conn = await Provider._makeConn()
        repo = EntryRepository(conn)
        try:
            yield repo
        finally:
            await conn.close()

    @staticmethod
    def serviceFor(route: EntityRoute):
        async def dependency(
            repository: EntryRepository = Depends(Provider.entryRepository)
        ) -> EntityService:
            return EntityService(route=route, repository=repository)
        return dependency