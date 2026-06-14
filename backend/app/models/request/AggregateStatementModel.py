from enum import Enum

from pydantic import BaseModel


class AggregateFunction(Enum):
    SUM = 'sum'
    MAX = 'max'
    MIN = 'min'
    AVG = 'avg'
    COUNT = 'count'

class AggregateStatementModel(BaseModel):
    by: str
    fn: AggregateFunction