from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import Provider
from app.models.analytics.AnalyticsModels import (
    CompareRequest,
    CompareResponse,
    CoverageResponse,
    HistogramRequest,
    HistogramResponse,
    SummaryRequest,
    SummaryResponse,
)
from app.services.analytics.AnalyticsService import AnalyticsService


class AnalyticsRouter:
    """Mounts /analytics/* endpoints for histogram, summary, compare, and coverage."""

    def __init__(self) -> None:
        self._router = APIRouter(prefix="/analytics", tags=["analytics"])

        @self._router.post("/histogram", response_model=HistogramResponse)
        async def histogram(
            body: HistogramRequest,
            service: AnalyticsService = Depends(Provider.analyticsService),
        ) -> HistogramResponse:
            return await service.histogram(body)

        @self._router.post("/summary", response_model=SummaryResponse)
        async def summary(
            body: SummaryRequest,
            service: AnalyticsService = Depends(Provider.analyticsService),
        ) -> SummaryResponse:
            return await service.summary(body)

        @self._router.post("/compare", response_model=CompareResponse)
        async def compare(
            body: CompareRequest,
            service: AnalyticsService = Depends(Provider.analyticsService),
        ) -> CompareResponse:
            return await service.compare(body)

        @self._router.get("/coverage", response_model=CoverageResponse)
        async def coverage(
            row_field: str = Query(default="process"),
            col_field: str = Query(default="ecm"),
            entry_type: str | None = Query(default=None),
            service: AnalyticsService = Depends(Provider.analyticsService),
        ) -> CoverageResponse:
            return await service.coverage(
                row_field=row_field,
                col_field=col_field,
                entry_type=entry_type,
            )

    @property
    def router(self) -> APIRouter:
        return self._router
