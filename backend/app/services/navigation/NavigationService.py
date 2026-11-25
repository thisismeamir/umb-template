from __future__ import annotations

from app.models.navigation.NavigationModels import (
    CATEGORY_TO_METADATA_KEY,
    FieldRegistryEntry,
    FieldRegistryResponse,
    NavigationCategory,
    NavigationItem,
    NavigationResponse,
)
from app.repositories.navigation.NavigationRepository import NavigationRepository


class NavigationService:
    """Orchestrates hierarchical physics navigation and dynamic field discovery."""

    def __init__(self, repository: NavigationRepository) -> None:
        self._repository = repository

    async def listCategory(
        self,
        category: NavigationCategory,
        *,
        entry_type: str | None = None,
    ) -> NavigationResponse:
        field_key = CATEGORY_TO_METADATA_KEY[category]
        rows = await self._repository.listFieldValues(
            field_key, entry_type=entry_type
        )
        items = [
            NavigationItem(
                name=str(row["name"]),
                count=int(row["count"]),
                entryTypes=list(row.get("entry_types") or []),
            )
            for row in rows
        ]
        return NavigationResponse(
            category=category.value,
            field=field_key,
            items=items,
            total=len(items),
        )

    async def listFieldValues(
        self,
        field_name: str,
        *,
        entry_type: str | None = None,
    ) -> NavigationResponse:
        rows = await self._repository.listFieldValues(
            field_name, entry_type=entry_type
        )
        items = [
            NavigationItem(
                name=str(row["name"]),
                count=int(row["count"]),
                entryTypes=list(row.get("entry_types") or []),
            )
            for row in rows
        ]
        return NavigationResponse(
            category="field",
            field=field_name,
            items=items,
            total=len(items),
        )

    async def listFields(
        self, *, entry_type: str | None = None
    ) -> FieldRegistryResponse:
        rows = await self._repository.listRegisteredFields(entry_type=entry_type)
        fields = [
            FieldRegistryEntry(
                entryType=str(row["entry_type"]),
                key=str(row["key"]),
                valueType=str(row["value_type"]),
                source=str(row["source"]),
            )
            for row in rows
        ]
        return FieldRegistryResponse(fields=fields, total=len(fields))
