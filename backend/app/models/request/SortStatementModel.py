from enum import Enum

from pydantic import BaseModel


class SortStatementOrder(Enum):
    ASC = 'asc'
    DESC = 'desc'

class SortStatementModel(BaseModel):
    by: str
    order: SortStatementOrder