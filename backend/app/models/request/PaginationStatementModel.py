from pydantic import BaseModel


class PaginationStatementModel(BaseModel):
    size: int
    cursor: str