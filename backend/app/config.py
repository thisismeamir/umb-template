# -----------------------------------------------------------------------------
#  FCC-Physics-Event : API Version 1
#
#  Copyright (c) 2026 CERN — Apache License 2.0
#  Developer: Kid A  |  amir.ebh@cern.ch
# -----------------------------------------------------------------------------
"""Application settings loaded from environment variables or .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    app_name: str = "fcc-physics-entities"
    api_version: str = "v1"
    debug: bool = False

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    databaseUser: str = Field("admin", alias="METADATA_BROWSER_POSTGRES_USER")
    databasePassword: str = Field("admin", alias="METADATA_BROWSER_POSTGRES_PASSWORD")
    databaseHost: str = Field("localhost", alias="METADATA_BROWSER_POSTGRES_HOST")
    databasePort: int = Field(5432, alias="METADATA_BROWSER_POSTGRES_PORT")
    databaseDatabase: str = Field(
        "universal_metadata_browser", alias="METADATA_BROWSER_POSTGRES_DB"
    )
    databasePoolMinSize: int = 2
    databasePoolMaxSize: int = 10
    databaseSchemaPath: str = "app/database/schema.sql"
    databaseSchemaAdvisoryLock: int = 1234567890
    databaseResetOnStartup: bool = False

    @property
    def databaseUrl(self) -> str:
        return (
            f"postgresql://{self.databaseUser}:{self.databasePassword}"
            f"@{self.databaseHost}:{self.databasePort}/{self.databaseDatabase}"
        )

    # ------------------------------------------------------------------
    # Auth (toggleable JWT / OIDC)
    # ------------------------------------------------------------------
    authEnabled: bool = Field(False, alias="METADATA_BROWSER_AUTH_ENABLED")
    authSecretKey: str = Field(
        "dev-insecure-change-me", alias="METADATA_BROWSER_APPLICATION_SECRET_KEY"
    )
    authAccessTokenMinutes: int = 60
    authRefreshTokenDays: int = 7
    authAdminUsers: list[str] = ["admin"]

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    cors_allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "https://fcc-physics.web.cern.ch",
    ]
    cors_allowed_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allowed_headers: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_max_age: int = 600

    # ------------------------------------------------------------------
    # Redis Worker Queue
    # ------------------------------------------------------------------
    broker_url: str = Field(
        "redis://localhost:6379/0", alias="METADATA_BROWSER_REDIS_URL"
    )
    result_backend: str = "redis://localhost:6379/1"
    workerQueueName: str = "umb:jobs:queue"
    workerProcessingQueueName: str = "umb:jobs:processing"
    workerPollTimeoutSeconds: int = 5

    fileWatcherRoot: str = "app/storage/data"


@lru_cache
def get_settings() -> Settings:
    return Settings()
