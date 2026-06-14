from enum import Enum


class Operator(Enum):
    EQUAL        = "="
    NOTEQUAL     = "!="
    GREATERTHAN  = ">"
    LESSTHAN     = "<"
    GREATEREQUAL = ">="
    LESSEQUAL    = "<="
    FUZZY        = "~"

