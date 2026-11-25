from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.request.where.unary.ListOperator import ListOperator
from app.models.request.where.unary.Value import Value


@dataclass
class ListStatement:
    operator: ListOperator
    values: list[Value[Any]]