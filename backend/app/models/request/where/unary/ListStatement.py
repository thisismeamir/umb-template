from dataclasses import dataclass
from typing import Generic, Any

from app.models.request.where.unary.ListOperator import ListOperator
from app.models.request.where.unary.Value import T, Value


@dataclass
class ListStatement:
    operator: ListOperator
    values: list[Value[Any]]