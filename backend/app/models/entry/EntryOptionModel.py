from enum import Enum

from pydantic import BaseModel


class EntryOptionType(str, Enum):
    TAKE = "take"
    TAKE_RANDOM = "take_random"
    SLICE = "slice"
    ONLY = "only"
    EXCLUDE = "exclude"
    SORT_ASC = "sort_asc"
    SORT_DESC = "sort_desc"
    UNIQUE = "unique"


class EntryOptionModel(BaseModel):
    key: str
    value: str
    type: EntryOptionType
