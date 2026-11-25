from __future__ import annotations

from app.engine.entry.EntityEngine import EntityEngine
from app.engine.export.ExportFormatters import ExportFormatters
from app.models.export.ExportModels import EXPORT_MEDIA_TYPES, ExportFormat
from app.models.request.EntityRequestModel import EntityRequestModel
from app.repositories.entry.EntityRepository import EntityRepository


class ExportService:
    """Executes an entity query and serializes matched entries into the requested format."""

    def __init__(self, repository: EntityRepository) -> None:
        self._repository = repository

    async def export(
        self,
        request: EntityRequestModel,
        fmt: ExportFormat,
    ) -> tuple[str, str, str]:
        """Return (payload_text, media_type, filename)."""
        engine = EntityEngine(request)
        plan = engine.executeRoot()
        rows = await self._repository.executeQuery(plan.sql, plan.params)
        page_rows, _, _ = engine.applyPagination(rows)
        sampled_rows = engine.applyGetClause(page_rows)
        final_rows = engine.applyTakeClause(sampled_rows)

        payload = ExportFormatters.render(fmt, final_rows)
        media_type, ext = EXPORT_MEDIA_TYPES[fmt]
        return payload, media_type, f"umb_export.{ext}"
