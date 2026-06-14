from fastapi import APIRouter

from .list import EventListRouter
from .query import EventQueryRouter
from .bulk import EventBulkRouter
from .detail import EventDetailRouter


class EventsRouter:
    def __init__(self):
        self._router = APIRouter(prefix="/entities", tags=["entities"])

        self._router.include_router(EventListRouter().router)
        self._router.include_router(EventQueryRouter().router)
        self._router.include_router(EventDetailRouter().router)
        self._router.include_router(EventBulkRouter().router)

    @property
    def router(self) -> APIRouter:
        return self._router