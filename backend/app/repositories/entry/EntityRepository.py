import asyncpg

import json
from typing import Any

import asyncpg


class EntityRepository:
    def __init__(self, db: asyncpg.Connection) -> None:
        self.db = db

    async def executeQuery(
        self,
        sql: str,
        params: list,
    ) -> list[dict[str, Any]]:
        rows = await self.db.fetch(sql, *params)

        return [
            {
                key: self._normalize(value)
                for key, value in dict(row).items()
            }
            for row in rows
        ]

    @staticmethod
    def _normalize(value: Any) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        if isinstance(value, list):
            return [EntityRepository._normalize(v) for v in value]

        if isinstance(value, dict):
            return {
                key: EntityRepository._normalize(v)
                for key, v in value.items()
            }

        return value
