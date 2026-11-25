from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ApiInformation(BaseModel):
    version: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    requestId: str = Field(default_factory=lambda: str(uuid4()))


class ValidationResult(BaseModel):
    valid: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def reject(self, message: str) -> None:
        self.valid = False
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


class AggregateResult(BaseModel):
    fn: str
    path: list[str]
    value: float | int | None


class DistinctResult(BaseModel):
    path: list[str]
    values: list[Any]


class VersionSummary(BaseModel):
    id: str
    version: int
    createdAt: datetime
    createdBy: str
    source: str


class Response(BaseModel):
    apiInformation: ApiInformation
    validationResult: ValidationResult
    status: str | None = "ok"
    # Normal query
    entities: list[dict[str, Any]] | None = None
    returned: int | None = None
    total: int | None = None

    # count clause
    count: int | None = None

    # aggregate clause
    aggregate: AggregateResult | None = None

    # distinct clause
    distinct: DistinctResult | None = None

    # versions clause
    versions: list[VersionSummary] | None = None

    # pagination
    nextCursor: str | None = None
    hasMore: bool | None = None
