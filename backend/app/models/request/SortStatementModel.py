from enum import Enum

from pydantic import BaseModel

from app.models.request.PathTrees import MetadataPathTree


class SortStatementOrder(Enum):
    ASC = 'asc'
    DESC = 'desc'

class SortStatementModel(BaseModel):
    by: MetadataPathTree
    order: SortStatementOrder