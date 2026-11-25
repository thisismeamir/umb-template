from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.api.dependencies import Provider
from app.models.auth.AuthModels import UserPrincipal
from app.models.collections.CollectionModels import (
    CollectionCreate,
    CollectionDetail,
    CollectionListResponse,
    CollectionUpdate,
    MembershipResponse,
    MembershipUpdate,
)
from app.services.collections.CollectionService import CollectionService


class CollectionRouter:
    """Mounts /collections/* CRUD and membership endpoints."""

    def __init__(self) -> None:
        self._router = APIRouter(prefix="/collections", tags=["collections"])

        @self._router.get("/", response_model=CollectionListResponse)
        async def listCollections(
            user: UserPrincipal = Depends(Provider.currentUser),
            service: CollectionService = Depends(Provider.collectionService),
        ) -> CollectionListResponse:
            return await service.listCollections(user)

        @self._router.post("/", response_model=CollectionDetail)
        async def createCollection(
            body: CollectionCreate,
            user: UserPrincipal = Depends(Provider.currentUser),
            service: CollectionService = Depends(Provider.collectionService),
        ) -> CollectionDetail:
            return await service.createCollection(body, user)

        @self._router.get("/{collection_id}", response_model=CollectionDetail)
        async def getCollection(
            collection_id: str,
            user: UserPrincipal = Depends(Provider.currentUser),
            service: CollectionService = Depends(Provider.collectionService),
        ) -> CollectionDetail:
            return await service.getCollection(collection_id, user)

        @self._router.put("/{collection_id}", response_model=CollectionDetail)
        async def updateCollection(
            collection_id: str,
            body: CollectionUpdate,
            user: UserPrincipal = Depends(Provider.currentUser),
            service: CollectionService = Depends(Provider.collectionService),
        ) -> CollectionDetail:
            return await service.updateCollection(collection_id, body, user)

        @self._router.delete("/{collection_id}")
        async def deleteCollection(
            collection_id: str,
            user: UserPrincipal = Depends(Provider.currentUser),
            service: CollectionService = Depends(Provider.collectionService),
        ) -> dict[str, Any]:
            return await service.deleteCollection(collection_id, user)

        @self._router.post("/{collection_id}/events", response_model=MembershipResponse)
        async def updateMembership(
            collection_id: str,
            body: MembershipUpdate,
            user: UserPrincipal = Depends(Provider.currentUser),
            service: CollectionService = Depends(Provider.collectionService),
        ) -> MembershipResponse:
            return await service.updateMembership(collection_id, body, user)

    @property
    def router(self) -> APIRouter:
        return self._router
