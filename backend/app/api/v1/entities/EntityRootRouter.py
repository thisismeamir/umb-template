from fastapi import APIRouter, Depends
from app.api.dependencies import Provider
from app.models.entity.EntityRoute import EntityRoute
from app.models.request.EntityRequestModel import EntityRequestModel

from app.services.entity.EntityService import EntityService
from app.repositories.entry.EntityRepository import EntityRepository


def makeServiceFor(route: EntityRoute):
    async def dependency(
        repository: EntityRepository = Depends(Provider.entryRepository)
    ) -> EntityService:
        return EntityService(route=route, repository=repository)
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

        @self._router.post("/get")
        async def get(
            body: EntityRequestModel,
            service: EntityService = Depends(makeServiceFor(EntityRoute.GET)),
        ):
            return await service.response(body)

        @self._router.get("/rand")
        async def random(
            body: EntityRequestModel,
            service: EntityService = Depends(makeServiceFor(EntityRoute.RAND)),
        ):
            return await service.response(body)

    @property
    def router(self) -> APIRouter:
        return self._router
