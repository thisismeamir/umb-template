from dataclasses import dataclass
from enum import Enum
from typing import TypeVar, Generic

T = TypeVar("T", int, float, str)

class ValueType(Enum):
    INTEGER = "INTEGER"
    DOUBLE = "DOUBLE"
    STRING = "STRING"
    SCIENTIFIC = "SCIENTIFIC"


@dataclass
class Value(Generic[T]):
    raw: str
    parsed: T