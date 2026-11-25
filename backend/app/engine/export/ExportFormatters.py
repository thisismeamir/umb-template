from __future__ import annotations

import csv
import io
import json
import pprint
from typing import Any

from app.models.export.ExportModels import ExportFormat


def _flattenRow(row: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested entity dict into dot-separated scalar columns for tabular export."""
    flat: dict[str, Any] = {}
    for k, v in row.items():
        key = f"{prefix}.{k}" if prefix else str(k)
        if isinstance(v, dict):
            flat.update(_flattenRow(v, key))
        elif isinstance(v, list):
            flat[key] = json.dumps(v, default=str)
        else:
            flat[key] = v
    return flat


def _yamlScalar(val: Any) -> str:
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    return json.dumps(str(val))


def _dumpYaml(obj: Any, indent: int = 0) -> list[str]:
    pad = " " * indent
    if isinstance(obj, dict):
        if not obj:
            return [f"{pad}{{}}"]
        lines: list[str] = []
        for k, v in obj.items():
            if isinstance(v, (dict, list)) and v:
                lines.append(f"{pad}{k}:")
                lines.extend(_dumpYaml(v, indent + 2))
            else:
                lines.append(f"{pad}{k}: {_yamlScalar(v)}")
        return lines
    if isinstance(obj, list):
        if not obj:
            return [f"{pad}[]"]
        lines = []
        for item in obj:
            if isinstance(item, dict) and item:
                sub = _dumpYaml(item, indent + 2)
                first = sub[0].lstrip()
                lines.append(f"{pad}- {first}")
                lines.extend(sub[1:])
            elif isinstance(item, list) and item:
                lines.append(f"{pad}-")
                lines.extend(_dumpYaml(item, indent + 2))
            else:
                lines.append(f"{pad}- {_yamlScalar(item)}")
        return lines
    return [f"{pad}{_yamlScalar(obj)}"]


def _tomlValue(val: Any) -> str:
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, list):
        inner = ", ".join(_tomlValue(v) for v in val if v is not None)
        return f"[{inner}]"
    return json.dumps(str(val))


class ExportFormatters:
    """Zero-dependency scientific data formatters (CSV, JSON, YAML, TOML, Python)."""

    @classmethod
    def render(cls, fmt: ExportFormat, rows: list[dict[str, Any]]) -> str:
        match fmt:
            case ExportFormat.CSV:
                return cls.formatCsv(rows)
            case ExportFormat.JSON:
                return cls.formatJson(rows)
            case ExportFormat.YAML:
                return cls.formatYaml(rows)
            case ExportFormat.TOML:
                return cls.formatToml(rows)
            case ExportFormat.PYTHON:
                return cls.formatPython(rows)
        raise ValueError(f"Unsupported export format: {fmt}")

    @staticmethod
    def formatCsv(rows: list[dict[str, Any]]) -> str:
        if not rows:
            return ""
        flattened = [_flattenRow(r) for r in rows]
        fieldnames: list[str] = sorted({k for r in flattened for k in r.keys()})
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in flattened:
            writer.writerow(r)
        return buf.getvalue()

    @staticmethod
    def formatJson(rows: list[dict[str, Any]]) -> str:
        return json.dumps(rows, indent=2, default=str)

    @staticmethod
    def formatYaml(rows: list[dict[str, Any]]) -> str:
        """Render rows as FCCAnalyses-friendly processList YAML keyed by name or id."""
        process_map: dict[str, Any] = {}
        for idx, row in enumerate(rows):
            meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else row
            key = str(meta.get("name") or row.get("id") or f"entry_{idx}")
            process_map[key] = meta
        return "\n".join(_dumpYaml({"processList": process_map})) + "\n"

    @staticmethod
    def formatToml(rows: list[dict[str, Any]]) -> str:
        """Render rows as a TOML [[entries]] array-of-tables document."""
        if not rows:
            return "entries = []\n"
        blocks: list[str] = []
        for row in rows:
            flat = _flattenRow(row)
            lines = ["[[entries]]"]
            for k in sorted(flat.keys()):
                v = flat[k]
                if v is None:
                    continue
                safe_key = k if k.replace("_", "").isalnum() else json.dumps(k)
                lines.append(f"{safe_key} = {_tomlValue(v)}")
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks) + "\n"

    @staticmethod
    def formatPython(rows: list[dict[str, Any]]) -> str:
        """Render rows as a ready-to-paste Python dictionary literal for notebooks."""
        process_dict: dict[str, Any] = {}
        for idx, row in enumerate(rows):
            meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else row
            key = str(meta.get("name") or row.get("id") or f"entry_{idx}")
            process_dict[key] = meta
        formatted = pprint.pformat(process_dict, indent=4, width=100, sort_dicts=True)
        return f"processList = {formatted}\n"
