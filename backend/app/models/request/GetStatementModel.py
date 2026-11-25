from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class GetStatementModel(BaseModel):
    first: int | None = Field(default=None, ge=0)
    last: int | None = Field(default=None, ge=0)
    random: int | None = Field(default=None, ge=0)
    uniform: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validateSingleMode(self) -> GetStatementModel:
        active = [
            name
            for name in ("first", "last", "random", "uniform")
            if getattr(self, name) is not None
        ]
        if len(active) > 1:
            raise ValueError(
                f"Specify at most one 'get' mode, got: {', '.join(active)}"
            )
        return self
