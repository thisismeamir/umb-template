from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class NavigationCategory(str, Enum):
    ACCELERATORS = "accelerators"
    CAMPAIGNS = "campaigns"
    DETECTORS = "detectors"
    STAGES = "stages"


CATEGORY_TO_METADATA_KEY: dict[NavigationCategory, str] = {
    NavigationCategory.ACCELERATORS: "accelerator",
    NavigationCategory.CAMPAIGNS: "campaign",
    NavigationCategory.DETECTORS: "detector",
    NavigationCategory.STAGES: "stage",
}


class NavigationItem(BaseModel):
    name: str
    count: int
    entryTypes: list[str] = Field(default_factory=list)


class NavigationResponse(BaseModel):
    category: str
    field: str
    items: list[NavigationItem]
    total: int


class FieldRegistryEntry(BaseModel):
    entryType: str
    key: str
    valueType: str
    source: str


class FieldRegistryResponse(BaseModel):
    fields: list[FieldRegistryEntry]
    total: int
