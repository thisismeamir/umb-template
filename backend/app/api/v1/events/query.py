from fastapi import APIRouter, Depends

from app.services.event_service import EventsService
from app.api.dependencies import get_events_service
from app.models.event.query import EventQuery
from app.models.event.response import EventListResponse


class EventQueryRouter:
    def __init__(self):
        self._router = APIRouter()
        @self._router.post("/query")
        async def query_events(
            query: EventQuery,
            service: EventsService = Depends(get_events_service),
        ):
            results = await service.search(query)

            return EventListResponse(
                results=results,
                limit=query.options.limit,
                offset=query.options.offset,
            )

    @property
    def router(self) -> APIRouter:
        return self._router