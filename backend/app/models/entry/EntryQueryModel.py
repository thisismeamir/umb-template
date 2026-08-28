from typing import List

from pydantic import BaseModel

from app.models.entry.EntryFieldModel import EntityFieldModel
from app.models.entry.EntryFilterModel import EntityFilterModel
from app.models.entry.EntryOptionModel import EntityOptionModel


class EntityQueryModel(BaseModel):
    entry_type: str
    fields:  List[EntityFieldModel]
    filters: List[EntityFilterModel]
    options: List[EntityOptionModel]
