from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from app.models.request.EntityRequestModel import EntityRequestModel


class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    PYTHON = "python"


EXPORT_MEDIA_TYPES: dict[ExportFormat, tuple[str, str]] = {
    ExportFormat.CSV: ("text/csv; charset=utf-8", "csv"),
    ExportFormat.JSON: ("application/json; charset=utf-8", "json"),
    ExportFormat.YAML: ("application/x-yaml; charset=utf-8", "yaml"),
    ExportFormat.TOML: ("application/toml; charset=utf-8", "toml"),
    ExportFormat.PYTHON: ("text/x-python; charset=utf-8", "py"),
}


class ExportRequest(BaseModel):
    query: EntityRequestModel
    format: ExportFormat = ExportFormat.JSON
