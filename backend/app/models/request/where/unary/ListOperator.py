from enum import Enum


class ListOperator(Enum):
    IN    = ":in"
    NOTIN = "!in"