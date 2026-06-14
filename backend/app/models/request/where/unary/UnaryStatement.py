from dataclasses import dataclass
from typing import Generic

from app.models.request.where.unary.Operator import Operator
from app.models.request.where.unary.Value import T, Value


@dataclass
class UnaryStatement(Generic[T]):
    operator: Operator
    value: Value[T]