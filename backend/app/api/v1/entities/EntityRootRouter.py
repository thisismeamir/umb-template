from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import Provider
from app.models.entity.EntityRoute import EntityRoute
from app.models.request.EntityRequestModel import EntityRequestModel
from app.models.response.response import Response
from app.services.entity.EntityService import EntityService


class EntityRootRouter:
    def __init__(self) -> None:
        self._router = APIRouter()

        @self._router.post("/", response_model=Response)
        async def root(
            body: EntityRequestModel,
            service: EntityService = Depends(Provider.serviceFor(EntityRoute.ROOT)),
        ) -> Response:
            return await service.response(body)

        @self._router.post("/query", response_model=Response)
        async def query(
            body: EntityRequestModel,
            service: EntityService = Depends(Provider.serviceFor(EntityRoute.QUERY)),
        ) -> Response:
            return await service.response(body)

        @self._router.post("/search", response_model=Response)
        async def search(
            body: EntityRequestModel,
            service: EntityService = Depends(Provider.serviceFor(EntityRoute.SEARCH)),
        ) -> Response:
            return await service.response(body)

        @self._router.post("/stat", response_model=Response)
        async def stat(
            body: EntityRequestModel,
            service: EntityService = Depends(Provider.serviceFor(EntityRoute.STAT)),
        ) -> Response:
            return await service.response(body)

        @self._router.post("/get", response_model=Response)
        async def get(
            body: EntityRequestModel,
            service: EntityService = Depends(Provider.serviceFor(EntityRoute.GET)),
        ) -> Response:
            return await service.response(body)

        @self._router.get("/rand", response_model=Response)
        async def random(
            n: int = Query(default=1, ge=1, le=100),
            entry_type: str | None = Query(default=None),
            service: EntityService = Depends(Provider.serviceFor(EntityRoute.RAND)),
        ) -> Response:
            request = EntityRequestModel(entry_type=entry_type)
            return await service.response(request, randLimit=n)

    @property
    def router(self) -> APIRouter:
        return self._router
