from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import Provider
from app.models.auth.AuthModels import UserPrincipal
from app.models.jobs.JobModels import (
    JobListResponse,
    JobRecord,
    JobResultResponse,
    JobSubmitRequest,
)
from app.services.jobs.JobService import JobService


class JobRouter:
    """Mounts /jobs/* endpoints backed by PostgreSQL + RedisJobQueue."""

    def __init__(self) -> None:
        self._router = APIRouter(prefix="/jobs", tags=["jobs"])

        @self._router.post("/", response_model=JobRecord)
        async def submitJob(
            body: JobSubmitRequest,
            user: UserPrincipal = Depends(Provider.currentUser),
            service: JobService = Depends(Provider.jobService),
        ) -> JobRecord:
            return await service.submit(body, user)

        @self._router.get("/", response_model=JobListResponse)
        async def listJobs(
            user: UserPrincipal = Depends(Provider.currentUser),
            service: JobService = Depends(Provider.jobService),
        ) -> JobListResponse:
            return await service.listJobs(user)

        @self._router.get("/{job_id}", response_model=JobRecord)
        async def getStatus(
            job_id: str,
            user: UserPrincipal = Depends(Provider.currentUser),
            service: JobService = Depends(Provider.jobService),
        ) -> JobRecord:
            return await service.getStatus(job_id, user)

        @self._router.get("/{job_id}/result", response_model=JobResultResponse)
        async def getResult(
            job_id: str,
            user: UserPrincipal = Depends(Provider.currentUser),
            service: JobService = Depends(Provider.jobService),
        ) -> JobResultResponse:
            return await service.getResult(job_id, user)

    @property
    def router(self) -> APIRouter:
        return self._router
