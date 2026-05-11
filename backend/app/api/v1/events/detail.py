from fastapi import APIRouter, Depends
from uuid import UUID

from app.services.event_service import EventsService
from app.api.dependencies import get_events_service
from app.models.event.response import Event


class EventDetailRouter:
    def __init__(self):
        self._router = APIRouter()

        @self._router.get("/{event_id}")
        async def get_event(
            event_id: UUID,
            service: EventsService = Depends(get_events_service),
        ):
            return await service.get(event_id)

    @property
    def router(self) -> APIRouter:
        return self._router