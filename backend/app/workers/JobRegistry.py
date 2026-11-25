from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.models.analytics.AnalyticsModels import HistogramRequest, SummaryRequest
from app.models.export.ExportModels import ExportFormat
from app.models.jobs.JobModels import JobTaskType
from app.models.request.EntityRequestModel import EntityRequestModel
from app.repositories.entry.EntityRepository import EntityRepository
from app.services.analytics.AnalyticsService import AnalyticsService
from app.services.export.ExportService import ExportService

TaskHandler = Callable[[dict[str, Any], EntityRepository], Awaitable[Any]]


async def _runExportTask(
    payload: dict[str, Any], repository: EntityRepository
) -> dict[str, Any]:
    fmt = ExportFormat(payload.get("format", ExportFormat.JSON.value))
    query_data = payload.get("query") or {}
    req = EntityRequestModel(**query_data)
    content, media_type, filename = await ExportService(repository).export(req, fmt)
    return {"filename": filename, "mediaType": media_type, "content": content}


async def _runHistogramTask(
    payload: dict[str, Any], repository: EntityRepository
) -> dict[str, Any]:
    req = HistogramRequest(**payload)
    resp = await AnalyticsService(repository).histogram(req)
    return resp.model_dump()


async def _runSummaryTask(
    payload: dict[str, Any], repository: EntityRepository
) -> dict[str, Any]:
    req = SummaryRequest(**payload)
    resp = await AnalyticsService(repository).summary(req)
    return resp.model_dump()


class JobRegistry:
    """Maps JobTaskType enums to async task execution callables."""

    _handlers: dict[JobTaskType, TaskHandler] = {
        JobTaskType.EXPORT: _runExportTask,
        JobTaskType.ANALYTICS_HISTOGRAM: _runHistogramTask,
        JobTaskType.ANALYTICS_SUMMARY: _runSummaryTask,
    }

    @classmethod
    def get(cls, task_type: JobTaskType) -> TaskHandler:
        if task_type not in cls._handlers:
            raise ValueError(f"No handler registered for task type '{task_type}'")
        return cls._handlers[task_type]
