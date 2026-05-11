
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class EventRepositoryRequestPlan:
    sql: str
    params: Dict[str, Any]