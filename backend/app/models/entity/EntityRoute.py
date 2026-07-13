from enum import Enum


class EntityRoute(str, Enum):
    ROOT    = "/"
    QUERY   = "/query"
    SEARCH  = "/search"
    STAT    = "/stat"
    HIST    = "/hist"
