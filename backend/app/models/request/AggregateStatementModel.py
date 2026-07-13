from enum import Enum

from pydantic import BaseModel

from app.models.request.PathTrees import MetadataPathTree


class AggregateFunction(Enum):
    SUM = 'sum'
    MAX = 'max'
    MIN = 'min'
    AVG = 'avg'
    COUNT = 'count'

class AggregateStatementModel(BaseModel):
    by: MetadataPathTree
    fn: AggregateFunction