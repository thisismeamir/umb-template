# -----------------------------------------------------------------------------
# FCC-Physics-Event : API Version 1
# Copyright (c) 2026 CERN — Apache License 2.0
# Developer: Kid A  |  amir.ebh@cern.ch
# -----------------------------------------------------------------------------
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencies import Provider
from app.api.middleware.logging import RequestLoggingMiddleware
from app.api.middleware.timing import TimingMiddleware
from app.api.v1.router import ApiV1
from app.config import get_settings
from app.database.DatabaseInitializer import DatabaseInitializer
from app.workers.FileWatcher import FileWatcher


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    pool = await Provider.initPool()
    Provider.getRedisQueue()

    async with pool.acquire() as initConn:
        await DatabaseInitializer(initConn).initialize(
            reset=settings.databaseResetOnStartup
        )

    watchConn = await Provider.makeConn()
    watcherTask = asyncio.create_task(FileWatcher(watchConn).scanAndWatch())

    try:
        yield
    finally:
        watcherTask.cancel()
        try:
            await watcherTask
        except asyncio.CancelledError:
            pass
        await watchConn.close()
        await Provider.closeRedisQueue()
        await Provider.closePool()


settings = get_settings()

app = FastAPI(
    title="Universal Metadata Browser API",
    description="Simple API for version 1 routes.",
    docs_url=None,
    lifespan=lifespan,
    openapi_url=None,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(TimingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allowed_methods,
    allow_headers=settings.cors_allowed_headers,
    max_age=settings.cors_max_age,
)

v1 = ApiV1()
app.mount("/api/v1", v1.as_subapp())
