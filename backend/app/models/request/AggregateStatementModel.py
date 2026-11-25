from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from app.models.request.PathTrees import MetadataPathTree


class AggregateFunction(str, Enum):
    SUM = "sum"
    MAX = "max"
    MIN = "min"
    AVG = "avg"
    COUNT = "count"


class AggregateStatementModel(BaseModel):
    by: MetadataPathTree
    fn: AggregateFunction
