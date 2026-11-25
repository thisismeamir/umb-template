from __future__ import annotations

from pydantic import BaseModel, Field


class PaginationStatementModel(BaseModel):
    size: int = Field(ge=1)
    cursor: str | None = None
