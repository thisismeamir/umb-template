from pydantic import BaseModel


class EntrySelectionStatementVersionsModel(BaseModel):
    selectionType: str | None
    value: str | int | None