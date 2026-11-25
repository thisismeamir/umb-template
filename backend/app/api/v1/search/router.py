from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import Provider
from app.models.search.SearchModels import (
    FulltextSearchResponse,
    SimilarSearchResponse,
    SuggestResponse,
)
from app.services.search.SearchService import SearchService


class SearchRouter:
    """Mounts /search/* endpoints for fulltext, similar entries, and autocomplete."""

    def __init__(self) -> None:
        self._router = APIRouter(prefix="/search", tags=["search"])

        @self._router.get("/", response_model=FulltextSearchResponse)
        async def fulltext(
            q: str = Query(..., min_length=1),
            entry_type: str | None = Query(default=None),
            limit: int = Query(default=25, ge=1, le=200),
            service: SearchService = Depends(Provider.searchService),
        ) -> FulltextSearchResponse:
            return await service.fulltext(q, entry_type=entry_type, limit=limit)

        @self._router.get("/similar/{entity_id}", response_model=SimilarSearchResponse)
        async def similar(
            entity_id: str,
            limit: int = Query(default=10, ge=1, le=100),
            service: SearchService = Depends(Provider.searchService),
        ) -> SimilarSearchResponse:
            return await service.similar(entity_id, limit=limit)

        @self._router.get("/suggest", response_model=SuggestResponse)
        async def suggest(
            field: str = Query(..., min_length=1),
            prefix: str = Query(default=""),
            entry_type: str | None = Query(default=None),
            limit: int = Query(default=15, ge=1, le=100),
            service: SearchService = Depends(Provider.searchService),
        ) -> SuggestResponse:
            return await service.suggest(
                field, prefix, entry_type=entry_type, limit=limit
            )

    @property
    def router(self) -> APIRouter:
        return self._router
