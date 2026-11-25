from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from app.models.request.PathTrees import MetadataPathTree


class SortStatementOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SortStatementModel(BaseModel):
    by: MetadataPathTree
    order: SortStatementOrder = SortStatementOrder.ASC
