from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.models.auth.AuthModels import UserPrincipal
from app.models.jobs.JobModels import (
    JobListResponse,
    JobRecord,
    JobResultResponse,
    JobStatus,
    JobSubmitRequest,
    JobTaskType,
)
from app.repositories.jobs.JobRepository import JobRepository
from app.workers.RedisJobQueue import JobQueueProtocol


class JobService:
    """Submits durable async jobs to PostgreSQL + RedisJobQueue and serves status/results."""

    def __init__(
        self,
        job_repository: JobRepository,
        job_queue: JobQueueProtocol,
    ) -> None:
        self._jobs = job_repository
        self._queue = job_queue

    @staticmethod
    def _toRecord(row: dict[str, Any]) -> JobRecord:
        return JobRecord(
            id=str(row["id"]),
            taskType=JobTaskType(row["task_type"]),
            status=JobStatus(row["status"]),
            owner=str(row["owner"]),
            error=row.get("error"),
            createdAt=row["created_at"],
            updatedAt=row["updated_at"],
        )

    @staticmethod
    def _canAccess(row: dict[str, Any], user: UserPrincipal) -> bool:
        return str(row["owner"]) == user.username or "admin" in user.roles

    async def submit(
        self,
        req: JobSubmitRequest,
        user: UserPrincipal,
    ) -> JobRecord:
        row = await self._jobs.create(
            task_type=req.taskType,
            owner=user.username,
            payload=req.payload,
        )
        job_id = str(row["id"])
        await self._queue.enqueue(job_id)
        return self._toRecord(row)

    async def listJobs(self, user: UserPrincipal) -> JobListResponse:
        rows = await self._jobs.listByOwner(user.username)
        records = [self._toRecord(r) for r in rows]
        return JobListResponse(jobs=records, total=len(records))

    async def getStatus(self, job_id: str, user: UserPrincipal) -> JobRecord:
        row = await self._jobs.getById(job_id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job '{job_id}' not found",
            )
        if not self._canAccess(row, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to job",
            )
        return self._toRecord(row)

    async def getResult(
        self, job_id: str, user: UserPrincipal
    ) -> JobResultResponse:
        row = await self._jobs.getById(job_id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job '{job_id}' not found",
            )
        if not self._canAccess(row, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to job",
            )
        return JobResultResponse(
            id=str(row["id"]),
            taskType=JobTaskType(row["task_type"]),
            status=JobStatus(row["status"]),
            result=row.get("result"),
            error=row.get("error"),
        )
