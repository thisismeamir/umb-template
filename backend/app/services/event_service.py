from typing import Protocol, List
from uuid import UUID

from app.engine.query.event_query_engine import EventQueryEngine
from app.engine.query.plan import EventRepositoryRequestPlan

from app.models.event.query import EventQuery, EventOptions
from app.models.event.response import Event, EventListResponse, BulkEventListResponse

from app.repository.event.read import EventReadRepository
from app.repository.event.mapper import EventMapper

class EventsService(Protocol):
    async def search(self, query: EventQuery) -> EventListResponse: ...
    async def get(self, event_id: UUID) -> Event: ...
    async def bulk_search(self, queries: List[EventQuery]) -> BulkEventListResponse: ...

class EventServiceImpl(EventsService):
    def __init__(
        self,
        repo: EventReadRepository,
        engine: EventQueryEngine,
    ):
        self.repo = repo
        self.engine = engine

    # ---------------------------------------------------------------------
    # SEARCH
    # ---------------------------------------------------------------------
    async def search(self, query: EventQuery) -> EventListResponse:
        plan: EventRepositoryRequestPlan = self.engine.compile(query)

        rows = await self.repo.execute(plan)

        events: List[Event] = [EventMapper.to_model(r) for r in rows]

        events = self._apply_projection(query.options, events)

        return EventListResponse(
            results=events,
            limit=query.options.limit,
            offset=query.options.offset,
        )

    # ---------------------------------------------------------------------
    # GET BY UUID
    # ---------------------------------------------------------------------
    async def get(self, event_id: UUID) -> Event:
        # You can either:
        # 1. Use a dedicated repo method
        # 2. Reuse the engine (less efficient)

        row = await self.repo.get_by_uuid(event_id)

        if row is None:
            # You may want a domain exception instead
            raise ValueError(f"Event {event_id} not found")

        return EventMapper.to_model(row)

    # ---------------------------------------------------------------------
    # BULK SEARCH
    # ---------------------------------------------------------------------
    async def bulk_search(
        self, queries: List[EventQuery]
    ) -> BulkEventListResponse:

        results: List[EventListResponse] = []

        for q in queries:
            res = await self.search(q)
            results.append(res)

        return BulkEventListResponse(results=results)

    # ---------------------------------------------------------------------
    # PROJECTION (only thing allowed post-query)
    # ---------------------------------------------------------------------
    def _apply_projection(
        self,
        options: EventOptions,
        events: List[Event],
    ) -> List[Event]:

        if not options.fields:
            return events

        allowed = set(options.fields)

        projected = []

        for e in events:
            data = e.model_dump()

            filtered = {k: v for k, v in data.items() if k in allowed}

            # NOTE:
            # This creates a *partial* Event.
            # If you want strict typing, introduce EventPartial model instead.
            projected.append(Event(**filtered))

        return projected