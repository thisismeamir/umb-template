import itertools
import re
from typing import Any
import random
from app.engine.entry.planner.SQLPlanner import SQLPlanner, SQLFragment
from app.models.request.EntityRequestModel import EntityRequestModel

class EntityEngine:
    def __init__(self, request: EntityRequestModel) -> None:
        self.request = request

    def executeRoot(self) -> SQLFragment:
        planner = SQLPlanner(self.request)
        return planner.generatePlan()

    def applyGetClause(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Post-fetch trimming/sampling of an already-filtered, already-sorted
        result set. Applied after EntityRepository.executeQuery returns rows
        for the plan produced by executeRoot().
        """
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
            if not rows:
                return []
            step = max(len(rows) // g.uniform, 1)
            return rows[::step][: g.uniform]
        return rows
