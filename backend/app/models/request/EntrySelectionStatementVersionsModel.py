from datetime import datetime
from pydantic import BaseModel, model_validator


class EntryRequestVersionsModel(BaseModel):
    last: int | None = None
    first: int | None = None
    by: str | None = None        # created_by filter
    type: str | None = None      # entry_type filter
    before: datetime | None = None
    after: datetime | None = None

    @model_validator(mode="after")
    def validateExclusivity(self) :
        if self.last is not None and self.first is not None:
            raise ValueError("Cannot specify both 'last' and 'first'")
        return self