from __future__ import annotations

import json
from typing import Any

from app.models.jobs.JobModels import JobStatus, JobTaskType


class JobRepository:
    """Data access for persistent async job records in PostgreSQL."""

    def __init__(self, db: Any) -> None:
        self.db = db

    async def create(
        self,
        *,
        task_type: JobTaskType,
        owner: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        sql = (
            "INSERT INTO jobs (task_type, status, owner, payload) "
            "VALUES ($1, $2, $3, $4) "
            "RETURNING id, task_type, status, owner, payload, result, error, created_at, updated_at"
        )
        rows = await self.db.fetch(
            sql,
            task_type.value,
            JobStatus.PENDING.value,
            owner,
            json.dumps(payload, default=str),
        )
        return dict(rows[0])

    async def getById(self, job_id: str) -> dict[str, Any] | None:
        sql = (
            "SELECT id, task_type, status, owner, payload, result, error, created_at, updated_at "
            "FROM jobs WHERE id = $1"
        )
        rows = await self.db.fetch(sql, job_id)
        if not rows:
            return None
        row = dict(rows[0])
        for json_col in ("payload", "result"):
            if isinstance(row.get(json_col), str):
                try:
                    row[json_col] = json.loads(row[json_col])
                except json.JSONDecodeError:
                    pass
        return row

    async def listByOwner(self, owner: str, *, limit: int = 50) -> list[dict[str, Any]]:
        sql = (
            "SELECT id, task_type, status, owner, error, created_at, updated_at "
            "FROM jobs WHERE owner = $1 ORDER BY created_at DESC LIMIT $2"
        )
        rows = await self.db.fetch(sql, owner, limit)
        return [dict(r) for r in rows]

    async def updateStatus(
        self,
        job_id: str,
        status: JobStatus,
        *,
        result: Any = None,
        error: str | None = None,
    ) -> None:
        sql = (
            "UPDATE jobs SET status = $1, result = $2, error = $3, updated_at = NOW() "
            "WHERE id = $4"
        )
        serialized = json.dumps(result, default=str) if result is not None else None
        await self.db.execute(sql, status.value, serialized, error, job_id)
