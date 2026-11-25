from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import Provider
from app.models.navigation.NavigationModels import (
    FieldRegistryResponse,
    NavigationCategory,
    NavigationResponse,
)
from app.services.navigation.NavigationService import NavigationService


class NavigationRouter:
    """Mounts /navigation/* endpoints for physics hierarchy and field discovery."""

    def __init__(self) -> None:
        self._router = APIRouter(prefix="/navigation", tags=["navigation"])

        @self._router.get("/accelerators", response_model=NavigationResponse)
        async def accelerators(
            entry_type: str | None = Query(default=None),
            service: NavigationService = Depends(Provider.navigationService),
        ) -> NavigationResponse:
            return await service.listCategory(
                NavigationCategory.ACCELERATORS, entry_type=entry_type
            )

        @self._router.get("/campaigns", response_model=NavigationResponse)
        async def campaigns(
            entry_type: str | None = Query(default=None),
            service: NavigationService = Depends(Provider.navigationService),
        ) -> NavigationResponse:
            return await service.listCategory(
                NavigationCategory.CAMPAIGNS, entry_type=entry_type
            )

        @self._router.get("/detectors", response_model=NavigationResponse)
        async def detectors(
            entry_type: str | None = Query(default=None),
            service: NavigationService = Depends(Provider.navigationService),
        ) -> NavigationResponse:
            return await service.listCategory(
                NavigationCategory.DETECTORS, entry_type=entry_type
            )

        @self._router.get("/stages", response_model=NavigationResponse)
        async def stages(
            entry_type: str | None = Query(default=None),
            service: NavigationService = Depends(Provider.navigationService),
        ) -> NavigationResponse:
            return await service.listCategory(
                NavigationCategory.STAGES, entry_type=entry_type
            )

        @self._router.get("/fields", response_model=FieldRegistryResponse)
        async def fields(
            entry_type: str | None = Query(default=None),
            service: NavigationService = Depends(Provider.navigationService),
        ) -> FieldRegistryResponse:
            return await service.listFields(entry_type=entry_type)

        @self._router.get("/values/{field_name}", response_model=NavigationResponse)
        async def fieldValues(
            field_name: str,
            entry_type: str | None = Query(default=None),
            service: NavigationService = Depends(Provider.navigationService),
        ) -> NavigationResponse:
            return await service.listFieldValues(field_name, entry_type=entry_type)

    @property
    def router(self) -> APIRouter:
        return self._router
