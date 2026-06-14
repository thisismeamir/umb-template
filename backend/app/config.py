# -----------------------------------------------------------------------------
#  FCC-Physics-Event : API Version 1
#
#  Copyright (c) 2026 CERN — Apache License 2.0
#  Developer: Kid A  |  amir.ebh@cern.ch
# -----------------------------------------------------------------------------
"""
Application settings.

Reads from environment variables or a .env file.
All middleware and service config comes from here — nothing is hardcoded.

Usage:
    from app.config import get_settings
    settings = get_settings()
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    app_name    : str  = "fcc-physics-entities"
    api_version : str  = "v1"
    debug       : bool = False

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    databaseUser : str = "username"
    databasePassword : str = "password"
    databaseHost : str = "localhost"
    databasePort : int = 5432
    databaseDatabase : str = "postgres"
    databaseSchemaPath: str = "app/database/schema.sql"
    databaseSchemaAdvisoryLock : int = 1234567890
    databaseUrl : str =  f"postgresql://{databaseUser}:{databasePassword}@{databaseHost}:{databasePort}/"
    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    cors_allowed_origins     : list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://fcc-physics.web.cern.ch",
    ]
    cors_allowed_methods     : list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allowed_headers     : list[str] = ["*"]
    cors_allow_credentials   : bool      = True
    cors_max_age             : int       = 600   # seconds browsers cache preflight

    # ------------------------------------------------------------------
    # Worker queue
    # ------------------------------------------------------------------
    broker_url   : str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/1"


@lru_cache
def get_settings() -> Settings:
    """
    Cached so the .env file is read once per process, not per request.
    Call get_settings.cache_clear() in test to reset between cases.
    """
    return Settings()