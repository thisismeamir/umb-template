from enum import Enum

from pydantic import BaseModel


class EntryFilterType(str, Enum):
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"
    IN_RANGE = "in_range"
    NOT_IN_RANGE = "not_in_range"

class EntryFilterModel(BaseModel):
    key: str
    value: str
    type: EntryFilterType
