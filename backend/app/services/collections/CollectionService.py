from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.models.auth.AuthModels import UserPrincipal
from app.models.collections.CollectionModels import (
    CollectionCreate,
    CollectionDetail,
    CollectionListResponse,
    CollectionSummary,
    CollectionUpdate,
    MembershipResponse,
    MembershipUpdate,
)
from app.repositories.collections.CollectionRepository import CollectionRepository


class CollectionService:
    """Enforces ownership/visibility and orchestrates collection CRUD + membership."""

    def __init__(self, repository: CollectionRepository) -> None:
        self._repository = repository

    @staticmethod
    def _toSummary(row: dict[str, Any], member_count: int | None = None) -> CollectionSummary:
        return CollectionSummary(
            id=str(row["id"]),
            name=str(row["name"]),
            description=str(row.get("description") or ""),
            owner=str(row["owner"]),
            isPublic=bool(row.get("is_public", False)),
            memberCount=(
                member_count
                if member_count is not None
                else int(row.get("member_count", 0))
            ),
            createdAt=row["created_at"],
            updatedAt=row["updated_at"],
        )

    @staticmethod
    def _canRead(row: dict[str, Any], user: UserPrincipal) -> bool:
        return (
            bool(row.get("is_public", False))
            or str(row["owner"]) == user.username
            or "admin" in user.roles
        )

    @staticmethod
    def _canWrite(row: dict[str, Any], user: UserPrincipal) -> bool:
        return str(row["owner"]) == user.username or "admin" in user.roles

    async def listCollections(self, user: UserPrincipal) -> CollectionListResponse:
        rows = await self._repository.listAccessible(user.username)
        items = [self._toSummary(r) for r in rows]
        return CollectionListResponse(collections=items, total=len(items))

    async def createCollection(
        self, req: CollectionCreate, user: UserPrincipal
    ) -> CollectionDetail:
        row = await self._repository.create(
            name=req.name,
            description=req.description,
            owner=user.username,
            is_public=req.isPublic,
        )
        summary = self._toSummary(row, member_count=0)
        return CollectionDetail(**summary.model_dump(), entryIds=[])

    async def getCollection(
        self, collection_id: str, user: UserPrincipal
    ) -> CollectionDetail:
        row = await self._repository.getById(collection_id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{collection_id}' not found",
            )
        if not self._canRead(row, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to private collection",
            )
        entry_ids = await self._repository.getEntryIds(collection_id)
        summary = self._toSummary(row, member_count=len(entry_ids))
        return CollectionDetail(**summary.model_dump(), entryIds=entry_ids)

    async def updateCollection(
        self, collection_id: str, req: CollectionUpdate, user: UserPrincipal
    ) -> CollectionDetail:
        existing = await self._repository.getById(collection_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{collection_id}' not found",
            )
        if not self._canWrite(existing, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the collection owner or admin may modify it",
            )
        updated = await self._repository.update(
            collection_id,
            name=req.name,
            description=req.description,
            is_public=req.isPublic,
        )
        assert updated is not None
        entry_ids = await self._repository.getEntryIds(collection_id)
        summary = self._toSummary(updated, member_count=len(entry_ids))
        return CollectionDetail(**summary.model_dump(), entryIds=entry_ids)

    async def deleteCollection(
        self, collection_id: str, user: UserPrincipal
    ) -> dict[str, Any]:
        existing = await self._repository.getById(collection_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{collection_id}' not found",
            )
        if not self._canWrite(existing, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the collection owner or admin may delete it",
            )
        deleted = await self._repository.delete(collection_id)
        return {"deleted": deleted, "id": collection_id}

    async def updateMembership(
        self, collection_id: str, req: MembershipUpdate, user: UserPrincipal
    ) -> MembershipResponse:
        existing = await self._repository.getById(collection_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{collection_id}' not found",
            )
        if not self._canWrite(existing, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the collection owner or admin may modify membership",
            )
        added = await self._repository.addEntries(
            collection_id, req.add, user.username
        )
        removed = await self._repository.removeEntries(collection_id, req.remove)
        entry_ids = await self._repository.getEntryIds(collection_id)
        return MembershipResponse(
            collectionId=collection_id,
            added=added,
            removed=removed,
            entryIds=entry_ids,
        )
