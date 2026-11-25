from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status

from app.engine.search.SearchEngine import SearchEngine
from app.models.search.SearchModels import (
    FulltextSearchResponse,
    SimilarSearchResponse,
    SuggestResponse,
)
from app.repositories.entry.EntityRepository import EntityRepository


class SearchService:
    """Orchestrates fulltext, similar-dataset, and autocomplete queries."""

    def __init__(self, repository: EntityRepository) -> None:
        self._repository = repository

    async def fulltext(
        self,
        query: str,
        *,
        entry_type: str | None = None,
        limit: int = 25,
    ) -> FulltextSearchResponse:
        params: list[Any] = [query, f"%{query}%"]
        extra_where = ""
        if entry_type is not None:
            extra_where = " AND entry_type = $3"
            params.append(entry_type)
            limit_placeholder = "$4"
        else:
            limit_placeholder = "$3"
        params.append(limit * 3)

        sql = (
            "SELECT id, entry_type, metadata, "
            "similarity(jsonb_values_to_text(metadata), $1) AS db_score "
            "FROM entries "
            "WHERE is_current = TRUE "
            "AND (similarity(jsonb_values_to_text(metadata), $1) > 0.15 "
            "OR jsonb_values_to_text(metadata) ILIKE $2)"
            f"{extra_where} "
            "ORDER BY db_score DESC "
            f"LIMIT {limit_placeholder}"
        )
        rows = await self._repository.executeQuery(sql, params)
        hits = SearchEngine.rankFulltext(query, rows, limit=limit)
        return FulltextSearchResponse(query=query, hits=hits, total=len(hits))

    async def similar(
        self,
        entity_id: str,
        *,
        limit: int = 10,
    ) -> SimilarSearchResponse:
        target_rows = await self._repository.executeQuery(
            "SELECT id, entry_type, metadata FROM entries WHERE id = $1 AND is_current = TRUE LIMIT 1",
            [entity_id],
        )
        if not target_rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entity '{entity_id}' not found",
            )
        target = target_rows[0]
        candidates = await self._repository.executeQuery(
            "SELECT id, entry_type, metadata FROM entries "
            "WHERE is_current = TRUE AND entry_type = $1 AND id <> $2 LIMIT 500",
            [target["entry_type"], entity_id],
        )
        hits = SearchEngine.rankSimilar(target, candidates, limit=limit)
        return SimilarSearchResponse(sourceId=entity_id, hits=hits, total=len(hits))

    async def suggest(
        self,
        field: str,
        prefix: str = "",
        *,
        entry_type: str | None = None,
        limit: int = 15,
    ) -> SuggestResponse:
        jsonpath = f"$.**.{json.dumps(field)}"
        params: list[Any] = [jsonpath, f"%{prefix}%"]
        extra_where = ""
        if entry_type is not None:
            extra_where = " AND entry_type = $3"
            params.append(entry_type)

        sql = (
            "SELECT DISTINCT val #>> '{}' AS value "
            "FROM entries, LATERAL jsonb_path_query(metadata, $1) AS val "
            "WHERE is_current = TRUE "
            "AND jsonb_typeof(val) NOT IN ('object', 'array', 'null') "
            f"AND (val #>> '{{}}') ILIKE $2{extra_where} "
            "LIMIT 200"
        )
        rows = await self._repository.executeQuery(sql, params)
        raw_values = [str(r["value"]) for r in rows if r.get("value") is not None]
        suggestions = SearchEngine.rankSuggestions(prefix, raw_values, limit=limit)
        return SuggestResponse(
            field=field,
            prefix=prefix,
            suggestions=suggestions,
            total=len(suggestions),
        )
