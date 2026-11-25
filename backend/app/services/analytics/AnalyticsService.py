from __future__ import annotations

from fastapi import HTTPException, status

from app.engine.analytics.AnalyticsEngine import AnalyticsEngine
from app.engine.entry.planner.SQLPlanner import SQLPlanner
from app.models.analytics.AnalyticsModels import (
    CompareRequest,
    CompareResponse,
    CoverageResponse,
    HistogramRequest,
    HistogramResponse,
    SummaryRequest,
    SummaryResponse,
)
from app.models.request.EntityRequestModel import EntityRequestModel
from app.repositories.entry.EntityRepository import EntityRepository
from app.utility.PathTreeToList import pathTreeToList


class AnalyticsService:
    """Orchestrates SQL retrieval and pure AnalyticsEngine computations."""

    def __init__(self, repository: EntityRepository) -> None:
        self._repository = repository

    async def histogram(self, request: HistogramRequest) -> HistogramResponse:
        paths = pathTreeToList(request.field)
        if len(paths) != 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="histogram 'field' must specify exactly one path",
            )
        query_req = EntityRequestModel(
            entry_type=request.entry_type,
            where=request.where,
            contains=request.field,
        )
        plan = SQLPlanner(query_req).generatePlan()
        rows = await self._repository.executeQuery(plan.sql, plan.params)
        return AnalyticsEngine.computeHistogram(rows, paths[0], bins=request.bins)

    async def summary(self, request: SummaryRequest) -> SummaryResponse:
        group_paths = pathTreeToList(request.groupBy)
        if len(group_paths) != 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="summary 'groupBy' must specify exactly one path",
            )
        metric_path: list[str] | None = None
        if request.metric is not None:
            m_paths = pathTreeToList(request.metric)
            if len(m_paths) != 1:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="summary 'metric' must specify exactly one path",
                )
            metric_path = m_paths[0]

        query_req = EntityRequestModel(
            entry_type=request.entry_type,
            where=request.where,
        )
        plan = SQLPlanner(query_req).generatePlan()
        rows = await self._repository.executeQuery(plan.sql, plan.params)
        return AnalyticsEngine.computeSummary(
            rows, group_paths[0], metricPath=metric_path
        )

    async def compare(self, request: CompareRequest) -> CompareResponse:
        metric_paths: list[list[str]] = []
        for tree in request.metrics:
            paths = pathTreeToList(tree)
            if len(paths) != 1:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Each entry in 'metrics' must specify exactly one path",
                )
            metric_paths.append(paths[0])

        planA = SQLPlanner(request.groupA).generatePlan()
        planB = SQLPlanner(request.groupB).generatePlan()
        rowsA = await self._repository.executeQuery(planA.sql, planA.params)
        rowsB = await self._repository.executeQuery(planB.sql, planB.params)
        return AnalyticsEngine.computeCompare(rowsA, rowsB, metric_paths)

    async def coverage(
        self,
        *,
        row_field: str = "process",
        col_field: str = "ecm",
        entry_type: str | None = None,
    ) -> CoverageResponse:
        row_path = [seg for seg in row_field.split(".") if seg]
        col_path = [seg for seg in col_field.split(".") if seg]
        if not row_path or not col_path:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Both 'row_field' and 'col_field' must be non-empty",
            )
        query_req = EntityRequestModel(entry_type=entry_type)
        plan = SQLPlanner(query_req).generatePlan()
        rows = await self._repository.executeQuery(plan.sql, plan.params)
        return AnalyticsEngine.computeCoverage(rows, row_path, col_path)
