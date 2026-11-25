from __future__ import annotations

from fastapi import APIRouter, Depends, Response as FastAPIResponse

from app.api.dependencies import Provider
from app.models.export.ExportModels import ExportFormat
from app.models.request.EntityRequestModel import EntityRequestModel
from app.services.export.ExportService import ExportService


class ExportRouter:
    """Mounts /export/{csv,json,yaml,toml,python} endpoints."""

    def __init__(self) -> None:
        self._router = APIRouter(prefix="/export", tags=["export"])

        async def _handle(
            body: EntityRequestModel,
            fmt: ExportFormat,
            service: ExportService,
        ) -> FastAPIResponse:
            payload, media_type, filename = await service.export(body, fmt)
            return FastAPIResponse(
                content=payload,
                media_type=media_type,
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                },
            )

        @self._router.post("/csv")
        async def exportCsv(
            body: EntityRequestModel,
            service: ExportService = Depends(Provider.exportService),
        ) -> FastAPIResponse:
            return await _handle(body, ExportFormat.CSV, service)

        @self._router.post("/json")
        async def exportJson(
            body: EntityRequestModel,
            service: ExportService = Depends(Provider.exportService),
        ) -> FastAPIResponse:
            return await _handle(body, ExportFormat.JSON, service)

        @self._router.post("/yaml")
        async def exportYaml(
            body: EntityRequestModel,
            service: ExportService = Depends(Provider.exportService),
        ) -> FastAPIResponse:
            return await _handle(body, ExportFormat.YAML, service)

        @self._router.post("/toml")
        async def exportToml(
            body: EntityRequestModel,
            service: ExportService = Depends(Provider.exportService),
        ) -> FastAPIResponse:
            return await _handle(body, ExportFormat.TOML, service)

        @self._router.post("/python")
        async def exportPython(
            body: EntityRequestModel,
            service: ExportService = Depends(Provider.exportService),
        ) -> FastAPIResponse:
            return await _handle(body, ExportFormat.PYTHON, service)

    @property
    def router(self) -> APIRouter:
        return self._router
