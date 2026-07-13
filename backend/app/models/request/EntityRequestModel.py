from __future__ import annotations
from pydantic import BaseModel

from app.models.request.AggregateStatementModel import AggregateStatementModel
from app.models.request.EntrySelectionStatementVersionsModel import EntrySelectionStatementVersionsModel
from app.models.request.GetStatementModel import GetStatementModel
from app.models.request.PaginationStatementModel import PaginationStatementModel
from app.models.request.PathTrees import MetadataPathTree, MetadataConditionTree
from app.models.request.SortStatementModel import SortStatementModel
from app.utility.PathTreeToList import pathTreeToList, conditionTreeToList


class EntityRequestModel(BaseModel):
    # Filter Model
    contains: MetadataPathTree | None = None
    without: MetadataPathTree | None = None
    take: MetadataPathTree | None = None
    where: MetadataConditionTree | None = None
    search: str | None = None
    get: GetStatementModel | None = None
    sort: SortStatementModel | None = None
    page: PaginationStatementModel | None = None
    aggregate: AggregateStatementModel | None = None
    distinct: MetadataPathTree | None = None
    count: bool | None = None

    # Entry Selection Model
    entry_type: list | None = None
    id: str | None = None
    version: str | None = None
    versions: EntrySelectionStatementVersionsModel | None = None
    snapshot: str | None = None

    from pydantic import model_validator

    @model_validator(mode="after")
    def validateTrees(self) -> EntityRequestModel:
        if self.contains is not None:
            pathTreeToList(self.contains)  # raises TypeError if malformed
        if self.where is not None:
            conditionTreeToList(self.where)  # raises TypeError if malformed
        return self

    

