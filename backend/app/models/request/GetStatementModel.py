from typing import Optional

from pydantic import BaseModel


class GetStatementModel(BaseModel):
    first: Optional[int] = 0
    last: Optional[int] = 0
    random: Optional[int] = 0
    uniform: Optional[int] = 0
