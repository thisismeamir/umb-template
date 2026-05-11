from app.engine.query.event_query_engine import EventRepositoryRequestPlan
from app.models.event.query import EventQuery



from typing import List
from app.models.event.response import Event


class EventReadRepository:
    def __init__(self, db):
        self.db = db  # e.g. asyncpg / sqlalchemy connection

    # TODO: Type of return should be written.
    async def execute(self, plan: EventRepositoryRequestPlan):
        rows = await self.db.fetch(plan.sql, **plan.params)

        return rows