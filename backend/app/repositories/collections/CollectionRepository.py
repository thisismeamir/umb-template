from __future__ import annotations

from typing import Any


class CollectionRepository:
    """Data access for user-owned collections and collection_memberships."""

    def __init__(self, db: Any) -> None:
        self.db = db

    async def listAccessible(self, owner: str) -> list[dict[str, Any]]:
        sql = (
            "SELECT c.id, c.name, c.description, c.owner, c.is_public, "
            "c.created_at, c.updated_at, COUNT(m.entry_id) AS member_count "
            "FROM collections c "
            "LEFT JOIN collection_memberships m ON m.collection_id = c.id "
            "WHERE c.owner = $1 OR c.is_public = TRUE "
            "GROUP BY c.id "
            "ORDER BY c.updated_at DESC"
        )
        rows = await self.db.fetch(sql, owner)
        return [dict(r) for r in rows]

    async def getById(self, collection_id: str) -> dict[str, Any] | None:
        sql = (
            "SELECT id, name, description, owner, is_public, created_at, updated_at "
            "FROM collections WHERE id = $1"
        )
        rows = await self.db.fetch(sql, collection_id)
        return dict(rows[0]) if rows else None

    async def getEntryIds(self, collection_id: str) -> list[str]:
        sql = (
            "SELECT entry_id FROM collection_memberships "
            "WHERE collection_id = $1 ORDER BY added_at ASC"
        )
        rows = await self.db.fetch(sql, collection_id)
        return [str(r["entry_id"]) for r in rows]

    async def create(
        self,
        *,
        name: str,
        description: str,
        owner: str,
        is_public: bool,
    ) -> dict[str, Any]:
        sql = (
            "INSERT INTO collections (name, description, owner, is_public) "
            "VALUES ($1, $2, $3, $4) "
            "RETURNING id, name, description, owner, is_public, created_at, updated_at"
        )
        rows = await self.db.fetch(sql, name, description, owner, is_public)
        return dict(rows[0])

    async def update(
        self,
        collection_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        is_public: bool | None = None,
    ) -> dict[str, Any] | None:
        sets: list[str] = ["updated_at = NOW()"]
        params: list[Any] = []
        if name is not None:
            params.append(name)
            sets.append(f"name = ${len(params)}")
        if description is not None:
            params.append(description)
            sets.append(f"description = ${len(params)}")
        if is_public is not None:
            params.append(is_public)
            sets.append(f"is_public = ${len(params)}")

        params.append(collection_id)
        sql = (
            f"UPDATE collections SET {', '.join(sets)} "
            f"WHERE id = ${len(params)} "
            "RETURNING id, name, description, owner, is_public, created_at, updated_at"
        )
        rows = await self.db.fetch(sql, *params)
        return dict(rows[0]) if rows else None

    async def delete(self, collection_id: str) -> bool:
        result = await self.db.execute(
            "DELETE FROM collections WHERE id = $1", collection_id
        )
        return str(result).endswith("1")

    async def addEntries(
        self, collection_id: str, entry_ids: list[str], added_by: str
    ) -> int:
        added = 0
        for eid in entry_ids:
            res = await self.db.execute(
                "INSERT INTO collection_memberships (collection_id, entry_id, added_by) "
                "VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                collection_id,
                eid,
                added_by,
            )
            if str(res).endswith("1"):
                added += 1
        return added

    async def removeEntries(
        self, collection_id: str, entry_ids: list[str]
    ) -> int:
        if not entry_ids:
            return 0
        res = await self.db.execute(
            "DELETE FROM collection_memberships "
            "WHERE collection_id = $1 AND entry_id = ANY($2)",
            collection_id,
            entry_ids,
        )
        parts = str(res).split()
        return int(parts[-1]) if parts and parts[-1].isdigit() else 0
