from fastapi import APIRouter

from app.api.v1.entities.EntityRootRouter import  EntityRootRouter


class EntityRouter:
    def __init__(self):
        self._router = APIRouter(prefix="/entity", tags=["entities"])
        self._router.include_router(EntityRootRouter().router)

    @property
    def router(self) -> APIRouter:
        return self._router