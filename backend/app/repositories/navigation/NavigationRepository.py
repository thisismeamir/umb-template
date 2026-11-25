from __future__ import annotations

import json
from typing import Any


class NavigationRepository:
    """Data access for navigation facets and field_registry introspection."""

    def __init__(self, db: Any) -> None:
        self.db = db

    async def listFieldValues(
        self,
        field_key: str,
        *,
        entry_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return distinct non-null scalar values for a metadata key with entry counts."""
        jsonpath = f"$.**.{json.dumps(field_key)}"
        params: list[Any] = [jsonpath]
        extra_where = ""
        if entry_type is not None:
            extra_where = " AND entry_type = $2"
            params.append(entry_type)

        sql = (
            "SELECT val #>> '{}' AS name, "
            "COUNT(DISTINCT id) AS count, "
            "ARRAY_AGG(DISTINCT entry_type ORDER BY entry_type) AS entry_types "
            "FROM entries, LATERAL jsonb_path_query(metadata, $1) AS val "
            f"WHERE is_current = TRUE AND jsonb_typeof(val) NOT IN ('object', 'array', 'null'){extra_where} "
            "GROUP BY name "
            "ORDER BY count DESC, name ASC"
        )
        rows = await self.db.fetch(sql, *params)
        return [dict(row) for row in rows]

    async def listRegisteredFields(
        self,
        *,
        entry_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """List discovered metadata fields from field_registry."""
        if entry_type is not None:
            sql = (
                "SELECT entry_type, key, value_type, source "
                "FROM field_registry "
                "WHERE entry_type = $1 "
                "ORDER BY entry_type ASC, key ASC"
            )
            rows = await self.db.fetch(sql, entry_type)
        else:
            sql = (
                "SELECT entry_type, key, value_type, source "
                "FROM field_registry "
                "ORDER BY entry_type ASC, key ASC"
            )
            rows = await self.db.fetch(sql)
        return [dict(row) for row in rows]
