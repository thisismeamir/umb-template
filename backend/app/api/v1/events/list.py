from fastapi import APIRouter, Depends, Request

from app.api.v1.builders.event_query_builder import EventQuery, EventQueryBuilder
from app.models.event.response import EventListResponse
from app.services.event_service import EventsService
from app.api.dependencies import get_events_service


class EventListRouter:
    def __init__(self):
        self._router = APIRouter()

        @self._router.get("")
        async def list_events(
            request: Request,
            service: EventsService = Depends(get_events_service),
        ):
            params = dict(request.query_params)

            query = EventQueryBuilder.from_dict(params)

            results = await service.search(query)

            return EventListResponse(
                results=results,
                limit=50,
                offset=0,
            )

    @property
    def router(self):
        return self._router