from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config import get_settings


class DatabaseInitializer:
    """Initializes PostgreSQL schema safely with an advisory lock."""

    def __init__(self, conn: Any) -> None:
        self.conn = conn

    async def initialize(self, reset: bool = False) -> None:
        """Apply schema DDL idempotently; only drop existing tables when reset=True."""
        settings = get_settings()
        lock_id = settings.databaseSchemaAdvisoryLock
        await self.conn.execute("SELECT pg_advisory_lock($1)", lock_id)
        try:
            if reset:
                await self._dropSchema()
            await self._createSchema()
        finally:
            await self.conn.execute("SELECT pg_advisory_unlock($1)", lock_id)

    async def _dropSchema(self) -> None:
        await self.conn.execute(
            """
            DROP TABLE IF EXISTS field_registry;
            DROP TABLE IF EXISTS entries;
            DROP FUNCTION IF EXISTS jsonb_values_to_text;
            DROP EXTENSION IF EXISTS pg_trgm;
            """
        )

    async def _createSchema(self) -> None:
        settings = get_settings()
        schema = Path(settings.databaseSchemaPath).read_text(encoding="utf-8")
        await self.conn.execute(schema)
