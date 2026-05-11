from typing import List

from app.engine.query.plan import EventRepositoryRequestPlan
from app.models.event.response import Event


class EventWriteRepository:
    def __init__(self, db):
        self.db = db  # e.g. asyncpg / sqlalchemy connection

    async def execute(self, plan: EventRepositoryRequestPlan) -> List[Event]:
        rows = await self.db.fetch(plan.sql, **plan.params)

        return [Event.model_validate(dict(row)) for row in rows]