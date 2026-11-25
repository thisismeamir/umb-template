from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.models.response.response import ApiInformation, Response, ValidationResult


class HealthRouter(APIRouter):
    def __init__(self) -> None:
        super().__init__()
        self._router = APIRouter(prefix="/check", tags=["system"])
        self._settings = get_settings()
        self.apiinfo = ApiInformation(version=self._settings.api_version)

        @self._router.get("/", response_model=Response)
        async def health() -> Response:
            return Response(
                apiInformation=self.apiinfo,
                validationResult=ValidationResult(),
            )

    @property
    def router(self) -> APIRouter:
        return self._router
