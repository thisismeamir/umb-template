from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SearchHit(BaseModel):
    id: str
    entryType: str
    score: float
    matchedFields: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FulltextSearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]
    total: int


class SimilarSearchResponse(BaseModel):
    sourceId: str
    hits: list[SearchHit]
    total: int


class SuggestResponse(BaseModel):
    field: str
    prefix: str
    suggestions: list[str]
    total: int
