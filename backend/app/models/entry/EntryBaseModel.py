from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EntryBaseModel(BaseModel):
    id: UUID
    version: int
    isCurrent: bool
    entryType: str
    source: str
    createdAt: datetime
    createdBy: str


