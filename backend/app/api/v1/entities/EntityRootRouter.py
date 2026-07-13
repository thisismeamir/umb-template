# api/v1/entities/EntityRootRouter.py

from fastapi import APIRouter, Depends

from app.models.entity.EntityRoute import EntityRoute
from app.models.request.EntityRequestModel import EntityRequestModel
from app.services.entity.EntityService import EntityService


def makeServiceFor(route: EntityRoute):
    def dependency() -> EntityService:
        return EntityService(route=route)
    return dependency


class EntityRootRouter:
    def __init__(self):
        self._router = APIRouter()

        @self._router.post("/")
        async def root(
            body: EntityRequestModel,
            service: EntityService = Depends(makeServiceFor(EntityRoute.ROOT)),
        ):
            return await service.response(body)

        @self._router.post("/query")
        async def query(
            body: EntityRequestModel,
            service: EntityService = Depends(makeServiceFor(EntityRoute.QUERY)),
        ):
            return await service.response(body)

        @self._router.post("/search")
        async def search(
            body: EntityRequestModel,
            service: EntityService = Depends(makeServiceFor(EntityRoute.SEARCH)),
        ):
            return await service.response(body)

        @self._router.post("/stat")
        async def stat(
            body: EntityRequestModel,
            service: EntityService = Depends(makeServiceFor(EntityRoute.STAT)),
        ):
            return await service.response(body)

        @self._router.post("/hist")
        async def hist(
            body: EntityRequestModel,
            service: EntityService = Depends(makeServiceFor(EntityRoute.HIST)),
        ):
            return await service.response(body)

    @property
    def router(self) -> APIRouter:
        return self._router