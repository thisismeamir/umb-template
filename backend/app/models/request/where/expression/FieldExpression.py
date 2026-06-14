from dataclasses import dataclass
from enum import Enum

from app.models.request.where.unary.ListStatement import ListStatement
from app.models.request.where.unary.UnaryStatement import UnaryStatement

type AnyStatement = (  UnaryStatement[int]
                     | UnaryStatement[float]
                     | UnaryStatement[str]
                     | ListStatement
                     )

@dataclass
class FieldExpression:
    statements: list[AnyStatement]
    operators: list[BooleanOperator]


class BooleanOperator(Enum):
    AND = "and"
    OR = "or"

type ExpressionChild = UnaryStatement | ListStatement | FieldExpression

@dataclass
class FieldExpression:
    children: list[ExpressionChild]
    operators: list[BooleanOperator | None]
