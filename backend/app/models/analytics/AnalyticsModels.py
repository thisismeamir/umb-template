from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.models.request.EntityRequestModel import EntityRequestModel
from app.models.request.PathTrees import MetadataConditionTree, MetadataPathTree


class HistogramRequest(BaseModel):
    field: MetadataPathTree
    bins: int = Field(default=10, ge=1, le=200)
    entry_type: str | list[str] | None = None
    where: MetadataConditionTree | None = None


class HistogramBin(BaseModel):
    lower: float
    upper: float
    count: int


class HistogramResponse(BaseModel):
    path: list[str]
    bins: list[HistogramBin]
    totalValues: int
    min: float | None = None
    max: float | None = None


class SummaryRequest(BaseModel):
    groupBy: MetadataPathTree
    metric: MetadataPathTree | None = None
    entry_type: str | list[str] | None = None
    where: MetadataConditionTree | None = None


class GroupedSummary(BaseModel):
    group: Any
    count: int
    sum: float | None = None
    mean: float | None = None
    min: float | None = None
    max: float | None = None


class SummaryResponse(BaseModel):
    groupBy: list[str]
    metric: list[str] | None = None
    groups: list[GroupedSummary]
    totalEntries: int


class CompareRequest(BaseModel):
    groupA: EntityRequestModel
    groupB: EntityRequestModel
    metrics: list[MetadataPathTree]


class MetricDelta(BaseModel):
    path: list[str]
    meanA: float | None = None
    meanB: float | None = None
    delta: float | None = None
    ratio: float | None = None


class CompareResponse(BaseModel):
    countA: int
    countB: int
    deltas: list[MetricDelta]


class CoverageCell(BaseModel):
    row: Any
    col: Any
    count: int


class CoverageResponse(BaseModel):
    rowField: list[str]
    colField: list[str]
    cells: list[CoverageCell]
    totalEntries: int
