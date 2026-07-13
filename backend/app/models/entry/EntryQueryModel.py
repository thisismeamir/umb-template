from typing import List

from pydantic import BaseModel

from app.models.entry.EntryFieldModel import EntryFieldModel
from app.models.entry.EntryFilterModel import EntryFilterModel
from app.models.entry.EntryOptionModel import EntryOptionModel


class EntryQueryModel(BaseModel):
    entry_type: str
    fields:  List[EntryFieldModel]
    filters: List[EntryFilterModel]
    options: List[EntryOptionModel]
