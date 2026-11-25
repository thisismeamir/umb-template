from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    isPublic: bool = False


class CollectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    isPublic: bool | None = None


class CollectionSummary(BaseModel):
    id: str
    name: str
    description: str
    owner: str
    isPublic: bool
    memberCount: int = 0
    createdAt: datetime
    updatedAt: datetime


class CollectionDetail(CollectionSummary):
    entryIds: list[str] = Field(default_factory=list)


class CollectionListResponse(BaseModel):
    collections: list[CollectionSummary]
    total: int


class MembershipUpdate(BaseModel):
    add: list[str] = Field(default_factory=list)
    remove: list[str] = Field(default_factory=list)


class MembershipResponse(BaseModel):
    collectionId: str
    added: int
    removed: int
    entryIds: list[str]
