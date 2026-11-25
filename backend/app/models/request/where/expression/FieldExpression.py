from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Union

from app.models.request.where.unary.ListStatement import ListStatement
from app.models.request.where.unary.UnaryStatement import UnaryStatement


class BooleanOperator(Enum):
    AND = "and"
    OR = "or"


ExpressionChild = Union[UnaryStatement, ListStatement, "FieldExpression"]


@dataclass
class FieldExpression:
    children: list[ExpressionChild]
    operators: list[BooleanOperator | None]
