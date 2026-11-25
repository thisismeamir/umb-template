from __future__ import annotations

from pydantic import BaseModel, model_validator

from app.models.request.AggregateStatementModel import AggregateStatementModel
from app.models.request.EntrySelectionStatementVersionsModel import (
    EntryRequestVersionsModel,
)
from app.models.request.GetStatementModel import GetStatementModel
from app.models.request.PaginationStatementModel import PaginationStatementModel
from app.models.request.PathTrees import MetadataConditionTree, MetadataPathTree
from app.models.request.SortStatementModel import SortStatementModel
from app.utility.PathTreeToList import conditionTreeToList, pathTreeToList


class EntityRequestModel(BaseModel):
    # Filter & Field Clauses
    contains: MetadataPathTree | None = None
    without: MetadataPathTree | None = None
    take: MetadataPathTree | None = None
    where: MetadataConditionTree | None = None
    search: str | None = None

    # Option Clauses
    get: GetStatementModel | None = None
    sort: SortStatementModel | None = None
    page: PaginationStatementModel | None = None
    aggregate: AggregateStatementModel | None = None
    distinct: MetadataPathTree | None = None
    count: bool | None = None

    # Entry Selection Clauses
    entry_type: str | list[str] | None = None
    id: str | None = None
    version: int | None = None
    versions: EntryRequestVersionsModel | None = None
    snapshot: str | None = None

    @model_validator(mode="after")
    def validateTrees(self) -> EntityRequestModel:
        for tree in (self.contains, self.without, self.take, self.distinct):
            if tree is not None:
                pathTreeToList(tree)
        if self.where is not None:
            conditionTreeToList(self.where)
        return self
