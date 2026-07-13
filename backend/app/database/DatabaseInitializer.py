
import asyncpg
from app.config import get_settings

class DatabaseInitializer:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn

    async def initialize(self) -> None:
        await self._dropSchema()
        await self._createSchema()

    async def _dropSchema(self) -> None:
        await self.conn.execute("""
            DROP TABLE IF EXISTS field_registry;
            DROP TABLE IF EXISTS entries;
            DROP FUNCTION IF EXISTS jsonb_values_to_text;
            DROP EXTENSION IF EXISTS pg_trgm;
        """)

    async def _createSchema(self) -> None:
        settings = get_settings()
        with open(settings.databaseSchemaPath, "r") as f:
            schema = f.read()
        await self.conn.execute(schema)