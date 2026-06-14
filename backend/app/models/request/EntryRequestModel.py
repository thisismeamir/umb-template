from __future__ import annotations
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, field_validator, model_validator

from app.models.request.AggregateStatementModel import AggregateStatementModel
from app.models.request.EntrySelectionStatementVersionsModel import EntrySelectionStatementVersionsModel
from app.models.request.GetStatementModel import GetStatementModel
from app.models.request.PaginationStatementModel import PaginationStatementModel
from app.models.request.SortStatementModel import SortStatementModel


class EntryRequestModel(BaseModel):
    # Filter Model
    contains: list | None
    without: list | None
    take: list | None
    where: dict[str,str] | None
    search: str | None
    get: GetStatementModel | None
    sort: SortStatementModel | None
    page: PaginationStatementModel | None
    aggregate: AggregateStatementModel | None
    distinct: str | None
    count: bool | None

    # Entry Selection Model
    entry_type: list | None
    id: str | None
    version: str | None
    versions: EntrySelectionStatementVersionsModel
    snapshot: str | None
