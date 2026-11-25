# -----------------------------------------------------------------------------
#  UMB Template Backend
#  Copyright (c) 2026 CERN
#  Licensed under the Apache License, Version 2.0
# -----------------------------------------------------------------------------
from __future__ import annotations

from collections.abc import AsyncIterator, Iterable
from enum import Enum
from typing import Any, Protocol

import asyncpg
from fastapi import APIRouter, FastAPI, Header, HTTPException, Request, status
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp

from app.config import get_settings
from app.models.auth.AuthModels import UserPrincipal
from app.models.entity.EntityRoute import EntityRoute
from app.repositories.collections.CollectionRepository import CollectionRepository
from app.repositories.entry.EntityRepository import EntityRepository
from app.repositories.jobs.JobRepository import JobRepository
from app.repositories.navigation.NavigationRepository import NavigationRepository
from app.services.analytics.AnalyticsService import AnalyticsService
from app.services.auth.AuthService import AuthService
from app.services.collections.CollectionService import CollectionService
from app.services.entity.EntityService import EntityService
from app.services.export.ExportService import ExportService
from app.services.jobs.JobService import JobService
from app.services.navigation.NavigationService import NavigationService
from app.services.search.SearchService import SearchService
from app.workers.RedisJobQueue import JobQueueProtocol, RedisJobQueue


class ApiState(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"  # fully removed -> 410


class RouterProvider(Protocol):
    @property
    def router(self) -> APIRouter: ...


def _reject_sunset(version: str, latest: str) -> Any:
    def _inner() -> None:
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


def _deprecation_headers_middleware(version: str) -> Any:
    async def middleware(request: Request, call_next: Any) -> Any:
        response = await call_next(request)
        response.headers["Deprecation"] = "true"
        response.headers["Warning"] = f'299 - "API {version} is deprecated"'
        return response

    return middleware


class Api:
    """Versioned API container with lifecycle-aware behavior."""

    def __init__(
        self,
        version: str,
        *,
        prefix: str = "/",
        state: ApiState = ApiState.ACTIVE,
        latest_version: str,
        dependencies: Iterable[Any] | None = None,
    ) -> None:
        self.version = version
        self.prefix = prefix
        self.state = state
        self.latest_version = latest_version
        self.dependencies = list(dependencies or [])
        self._mounted = False

        if self.state == ApiState.SUNSET:
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
        tags: list[str] | None = None,
    ) -> None:
        if self._mounted:
            raise RuntimeError("Cannot include routers after mounting")
        self._router.include_router(router, prefix=prefix, tags=tags)

    def mount(self, app: FastAPI) -> None:
        if self._mounted:
            raise RuntimeError("API already mounted")

        if self.state == ApiState.DEPRECATED:
            app.middleware("http")(_deprecation_headers_middleware(self.version))

        app.include_router(self._router)
        self._mounted = True

    def as_subapp(self) -> ASGIApp:
        sub = FastAPI(
            title=f"API {self.version}",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
        )

        if self.state == ApiState.SUNSET:

            @sub.middleware("http")
            async def reject_all(_request: Request, _call_next: Any) -> JSONResponse:
                return JSONResponse(
                    status_code=410,
                    content=self.gone(),
                )
        else:
            if self.state == ApiState.DEPRECATED:
                sub.middleware("http")(_deprecation_headers_middleware(self.version))
            sub.include_router(self._router)

        return sub

    def gone(self) -> dict[str, str]:
        return {
            "error": "deprecated_api_version",
            "message": f"{self.version} is no longer supported",
            "current_version": self.latest_version,
            "docs": f"/docs/{self.latest_version}",
        }


# -----------------------------------------------------------------------------
# FastAPI Dependency Callables (module-level functions so Depends() resolves globals)
# -----------------------------------------------------------------------------


async def _dbConnection() -> AsyncIterator[Any]:
    if Provider._pool is not None:
        async with Provider._pool.acquire() as conn:
            yield conn
    else:
        conn = await Provider.makeConn()
        try:
            yield conn
        finally:
            await conn.close()


async def _entryRepository(
    conn: Any = Depends(_dbConnection),
) -> EntityRepository:
    return EntityRepository(conn)


async def _navigationRepository(
    conn: Any = Depends(_dbConnection),
) -> NavigationRepository:
    return NavigationRepository(conn)


async def _collectionRepository(
    conn: Any = Depends(_dbConnection),
) -> CollectionRepository:
    return CollectionRepository(conn)


async def _jobRepository(
    conn: Any = Depends(_dbConnection),
) -> JobRepository:
    return JobRepository(conn)


async def _jobQueue() -> JobQueueProtocol:
    return Provider.getRedisQueue()


async def _authService() -> AuthService:
    return AuthService(get_settings())


async def _currentUser(
    authorization: str | None = Header(default=None),
    auth: AuthService = Depends(_authService),
) -> UserPrincipal:
    return auth.resolvePrincipal(authorization)


async def _navigationService(
    repository: NavigationRepository = Depends(_navigationRepository),
) -> NavigationService:
    return NavigationService(repository=repository)


async def _searchService(
    repository: EntityRepository = Depends(_entryRepository),
) -> SearchService:
    return SearchService(repository=repository)


async def _analyticsService(
    repository: EntityRepository = Depends(_entryRepository),
) -> AnalyticsService:
    return AnalyticsService(repository=repository)


async def _exportService(
    repository: EntityRepository = Depends(_entryRepository),
) -> ExportService:
    return ExportService(repository=repository)


async def _collectionService(
    repository: CollectionRepository = Depends(_collectionRepository),
) -> CollectionService:
    return CollectionService(repository=repository)


async def _jobService(
    job_repo: JobRepository = Depends(_jobRepository),
    queue: JobQueueProtocol = Depends(_jobQueue),
) -> JobService:
    return JobService(job_repository=job_repo, job_queue=queue)


class Provider:
    """Manages shared asyncpg pool, RedisJobQueue, and FastAPI dependency factories."""

    _pool: asyncpg.Pool | None = None
    _redis_queue: JobQueueProtocol | None = None

    dbConnection = staticmethod(_dbConnection)
    entryRepository = staticmethod(_entryRepository)
    navigationRepository = staticmethod(_navigationRepository)
    collectionRepository = staticmethod(_collectionRepository)
    jobRepository = staticmethod(_jobRepository)
    jobQueue = staticmethod(_jobQueue)
    authService = staticmethod(_authService)
    currentUser = staticmethod(_currentUser)
    navigationService = staticmethod(_navigationService)
    searchService = staticmethod(_searchService)
    analyticsService = staticmethod(_analyticsService)
    exportService = staticmethod(_exportService)
    collectionService = staticmethod(_collectionService)
    jobService = staticmethod(_jobService)

    @classmethod
    async def initPool(cls) -> asyncpg.Pool:
        if cls._pool is None:
            settings = get_settings()
            cls._pool = await asyncpg.create_pool(
                host=settings.databaseHost,
                port=settings.databasePort,
                user=settings.databaseUser,
                password=settings.databasePassword,
                database=settings.databaseDatabase,
                min_size=settings.databasePoolMinSize,
                max_size=settings.databasePoolMaxSize,
            )
        return cls._pool

    @classmethod
    async def closePool(cls) -> None:
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    def getRedisQueue(cls) -> JobQueueProtocol:
        if cls._redis_queue is None:
            settings = get_settings()
            cls._redis_queue = RedisJobQueue.fromUrl(
                settings.broker_url,
                queue_key=settings.workerQueueName,
                processing_key=settings.workerProcessingQueueName,
            )
        return cls._redis_queue

    @classmethod
    async def closeRedisQueue(cls) -> None:
        if cls._redis_queue is not None:
            await cls._redis_queue.close()
            cls._redis_queue = None

    @staticmethod
    async def makeConn() -> asyncpg.Connection:
        settings = get_settings()
        return await asyncpg.connect(
            host=settings.databaseHost,
            port=settings.databasePort,
            user=settings.databaseUser,
            password=settings.databasePassword,
            database=settings.databaseDatabase,
        )

    @staticmethod
    def serviceFor(route: EntityRoute) -> Any:
        async def dependency(
            repository: EntityRepository = Depends(_entryRepository),
        ) -> EntityService:
            return EntityService(route=route, repository=repository)

        return dependency
