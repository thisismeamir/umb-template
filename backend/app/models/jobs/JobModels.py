from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class JobTaskType(str, Enum):
    EXPORT = "export"
    ANALYTICS_HISTOGRAM = "analytics_histogram"
    ANALYTICS_SUMMARY = "analytics_summary"


class JobSubmitRequest(BaseModel):
    taskType: JobTaskType
    payload: dict[str, Any] = Field(default_factory=dict)


class JobRecord(BaseModel):
    id: str
    taskType: JobTaskType
    status: JobStatus
    owner: str
    error: str | None = None
    createdAt: datetime
    updatedAt: datetime


class JobResultResponse(BaseModel):
    id: str
    taskType: JobTaskType
    status: JobStatus
    result: Any = None
    error: str | None = None


class JobListResponse(BaseModel):
    jobs: list[JobRecord]
    total: int
