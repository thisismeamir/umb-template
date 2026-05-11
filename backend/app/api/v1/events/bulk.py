from fastapi import APIRouter, Depends
from typing import List

from app.services.event_service import EventsService
from app.api.dependencies import get_events_service
from app.models.event.query import EventQuery
from app.models.event.response import BulkEventListResponse, EventListResponse


class EventBulkRouter:
    def __init__(self):
        self._router = APIRouter()

        @self._router.post("/bulk")
        async def bulk_events(
            queries: List[EventQuery],
            service: EventsService = Depends(get_events_service),
        ):
            results = await service.bulk_search(queries)

            return BulkEventListResponse(
                results=[
                    EventListResponse(results=r, limit=0, offset=0)
                    for r in results
                ]
            )

    @property
    def router(self) -> APIRouter:
        return self._router