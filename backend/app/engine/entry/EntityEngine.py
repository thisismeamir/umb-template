from __future__ import annotations

import random
from typing import Any

from app.engine.entry.planner.SQLPlanner import SQLFragment, SQLPlanner
from app.models.request.EntityRequestModel import EntityRequestModel
from app.utility.PathTreeToList import pathTreeToList


class EntityEngine:
    """Executes query planning and post-fetch transformations for entity requests."""

    def __init__(self, request: EntityRequestModel) -> None:
        self.request = request
        self._planner = SQLPlanner(request)

    def executeRoot(self) -> SQLFragment:
        return self._planner.generatePlan()

    def executeCount(self) -> SQLFragment:
        return self._planner.generateCountPlan()

    def executeAggregate(self) -> tuple[list[str], SQLFragment]:
        return self._planner.generateAggregatePlan()

    def executeDistinct(self) -> tuple[list[str], SQLFragment]:
        return self._planner.generateDistinctPlan()

    def executeVersions(self) -> SQLFragment:
        return self._planner.generateVersionsPlan()

    def executeRandom(self, limit: int = 1) -> SQLFragment:
        return self._planner.generateRandomPlan(limit=limit)

    def applyGetClause(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Post-fetch trimming/sampling of an already-filtered, already-sorted result set."""
        g = self.request.get
        if g is None:
            return rows
        if g.first is not None:
            return rows[: g.first]
        if g.last is not None:
            return rows[-g.last :] if g.last > 0 else []
        if g.random is not None:
            return random.sample(rows, min(g.random, len(rows)))
        if g.uniform is not None:
            if not rows or g.uniform == 0:
                return []
            step = max(len(rows) // g.uniform, 1)
            return rows[::step][: g.uniform]
        return rows

    def applyTakeClause(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Project each row's metadata to only the paths requested in 'take', preserving hierarchy."""
        if self.request.take is None:
            return rows
        paths = pathTreeToList(self.request.take)
        projected: list[dict[str, Any]] = []
        for row in rows:
            new_row = dict(row)
            meta = row.get("metadata")
            if isinstance(meta, dict):
                new_row["metadata"] = self._projectDict(meta, paths)
            projected.append(new_row)
        return projected

    def applyPagination(
        self, rows: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], str | None, bool | None]:
        """Trim over-fetched page rows (size + 1) and return (pageRows, nextCursor, hasMore)."""
        if self.request.page is None:
            return rows, None, None
        size = self.request.page.size
        hasMore = len(rows) > size
        pageRows = rows[:size]
        nextCursor = (
            str(pageRows[-1]["id"])
            if hasMore and pageRows and "id" in pageRows[-1]
            else None
        )
        return pageRows, nextCursor, hasMore

    @staticmethod
    def _projectDict(source: dict[str, Any], paths: list[list[str]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for path in paths:
            cursor: Any = source
            found = True
            for segment in path:
                if isinstance(cursor, dict) and segment in cursor:
                    cursor = cursor[segment]
                else:
                    found = False
                    break
            if not found:
                continue
            target = result
            for segment in path[:-1]:
                target = target.setdefault(segment, {})
            target[path[-1]] = cursor
        return result
