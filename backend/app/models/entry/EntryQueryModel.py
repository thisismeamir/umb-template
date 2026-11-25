from __future__ import annotations

from pydantic import BaseModel

from app.models.entry.EntryFieldModel import EntryFieldModel
from app.models.entry.EntryFilterModel import EntryFilterModel
from app.models.entry.EntryOptionModel import EntryOptionModel


class EntryQueryModel(BaseModel):
    entry_type: str
    fields: list[EntryFieldModel]
    filters: list[EntryFilterModel]
    options: list[EntryOptionModel]
