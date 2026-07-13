# -----------------------------------------------------------------------------
import asyncio
from contextlib import asynccontextmanager

import asyncpg
# FCC-Physics-Event : API Version 1

# Copyright (c) 2026 CERN — Apache License 2.0

# Developer: Kid A  |  amir.ebh@cern.ch

# -----------------------------------------------------------------------------

from fastapi import FastAPI
from app.api.v1.router import ApiV1
from app.config import Settings, get_settings
from app.database.DatabaseInitializer import DatabaseInitializer
from app.workers.FileWatcher import FileWatcher


# ------------------------------------------------------------------

# App initialization

# ------------------------------------------------------------------
async def makeConn() -> asyncpg.Connection:
    settings = get_settings()
    return await asyncpg.connect(
        host=settings.databaseHost,
        port=settings.databasePort,
        user=settings.databaseUser,
        password=settings.databasePassword,
        database=settings.databaseDatabase
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    initConn = await makeConn()
    await DatabaseInitializer(initConn).initialize()
    await initConn.close()

    watchConn = await makeConn()
    asyncio.create_task(FileWatcher(watchConn).scanAndWatch())

    yield

    await watchConn.close()


app = FastAPI(
title="Universal Metadata Browser API",
description="Simple API for version 1 routes.",
docs_url=None,
lifespan=lifespan,
openapi_url=None
)

# ------------------------------------------------------------------

# Routers

# ------------------------------------------------------------------

v1 = ApiV1()

app.mount("/api/v1",v1.as_subapp())