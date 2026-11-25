from __future__ import annotations

import ast
import asyncio
import csv
import io
import json
import unittest
from typing import Any

from app.engine.analytics.AnalyticsEngine import AnalyticsEngine
from app.engine.export.ExportFormatters import ExportFormatters
from app.engine.search.SearchEngine import SearchEngine
from app.models.analytics.AnalyticsModels import (
    CompareRequest,
    HistogramRequest,
    SummaryRequest,
)
from app.models.export.ExportModels import ExportFormat
from app.models.navigation.NavigationModels import NavigationCategory
from app.models.request.EntityRequestModel import EntityRequestModel
from app.services.analytics.AnalyticsService import AnalyticsService
from app.services.export.ExportService import ExportService
from app.services.navigation.NavigationService import NavigationService
from app.services.search.SearchService import SearchService


class FakeEntityRepository:
    def __init__(self, responses: list[list[dict[str, Any]]]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, list[Any]]] = []

    async def executeQuery(
        self, sql: str, params: list[Any]
    ) -> list[dict[str, Any]]:
        self.calls.append((sql, params))
        if len(self._responses) > 1:
            return self._responses.pop(0)
        return self._responses[0] if self._responses else []


class FakeNavigationRepository:
    def __init__(
        self,
        values: list[dict[str, Any]] | None = None,
        fields: list[dict[str, Any]] | None = None,
    ) -> None:
        self._values = values or []
        self._fields = fields or []
        self.calls: list[tuple[str, str | None]] = []

    async def listFieldValues(
        self, field_key: str, *, entry_type: str | None = None
    ) -> list[dict[str, Any]]:
        self.calls.append((field_key, entry_type))
        return self._values

    async def listRegisteredFields(
        self, *, entry_type: str | None = None
    ) -> list[dict[str, Any]]:
        self.calls.append(("__fields__", entry_type))
        return self._fields


SAMPLE_ROWS: list[dict[str, Any]] = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "entry_type": "collision",
        "metadata": {
            "name": "wzp6_ee_ZH_ecm240",
            "process": "ee_ZH",
            "ecm": 240.0,
            "generator": "Whizard",
            "campaign": "winter2023",
            "detector": "IDEA",
            "cross_section_pb": 0.201,
        },
    },
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "entry_type": "collision",
        "metadata": {
            "name": "wzp6_ee_ZH_ecm365",
            "process": "ee_ZH",
            "ecm": 365.0,
            "generator": "Whizard",
            "campaign": "spring2024",
            "detector": "IDEA",
            "cross_section_pb": 0.128,
        },
    },
    {
        "id": "00000000-0000-0000-0000-000000000003",
        "entry_type": "collision",
        "metadata": {
            "name": "p8_ee_WW_ecm240",
            "process": "ee_WW",
            "ecm": 240.0,
            "generator": "Pythia8",
            "campaign": "winter2023",
            "detector": "CLD",
            "cross_section_pb": 16.438,
        },
    },
]


class TestNavigationModule(unittest.TestCase):
    def test_navigation_categories_and_fields(self) -> None:
        async def run() -> None:
            repo = FakeNavigationRepository(
                values=[
                    {"name": "winter2023", "count": 12, "entry_types": ["collision"]},
                    {"name": "spring2024", "count": 5, "entry_types": ["collision"]},
                ],
                fields=[
                    {
                        "entry_type": "collision",
                        "key": "ecm",
                        "value_type": "float",
                        "source": "DIRAC",
                    }
                ],
            )
            svc = NavigationService(repo)  # type: ignore[arg-type]

            campaigns = await svc.listCategory(
                NavigationCategory.CAMPAIGNS, entry_type="collision"
            )
            self.assertEqual(campaigns.category, "campaigns")
            self.assertEqual(campaigns.field, "campaign")
            self.assertEqual(campaigns.total, 2)
            self.assertEqual(campaigns.items[0].name, "winter2023")

            fields = await svc.listFields(entry_type="collision")
            self.assertEqual(fields.total, 1)
            self.assertEqual(fields.fields[0].key, "ecm")

        asyncio.run(run())


class TestSearchModule(unittest.TestCase):
    def test_fulltext_similarity_and_suggest_engines(self) -> None:
        hits = SearchEngine.rankFulltext("Whizard", SAMPLE_ROWS, limit=10)
        self.assertEqual(len(hits), 2)
        self.assertTrue(all("generator" in h.matchedFields for h in hits))

        similar = SearchEngine.rankSimilar(SAMPLE_ROWS[0], SAMPLE_ROWS, limit=5)
        self.assertEqual(len(similar), 2)
        # Same process + generator + detector should outrank ee_WW
        self.assertEqual(similar[0].id, SAMPLE_ROWS[1]["id"])

        suggestions = SearchEngine.rankSuggestions(
            "win", ["spring2024", "winter2023", "pre_winter"], limit=5
        )
        self.assertEqual(suggestions, ["winter2023", "pre_winter"])

    def test_search_service_end_to_end(self) -> None:
        async def run() -> None:
            repo = FakeEntityRepository([SAMPLE_ROWS])
            svc = SearchService(repo)  # type: ignore[arg-type]
            resp = await svc.fulltext("ee_ZH", limit=10)
            self.assertEqual(resp.total, 2)

            sim_repo = FakeEntityRepository([[SAMPLE_ROWS[0]], SAMPLE_ROWS[1:]])
            sim_svc = SearchService(sim_repo)  # type: ignore[arg-type]
            sim_resp = await sim_svc.similar(SAMPLE_ROWS[0]["id"], limit=5)
            self.assertEqual(sim_resp.sourceId, SAMPLE_ROWS[0]["id"])
            self.assertEqual(sim_resp.hits[0].id, SAMPLE_ROWS[1]["id"])

        asyncio.run(run())


class TestAnalyticsModule(unittest.TestCase):
    def test_histogram_summary_compare_and_coverage(self) -> None:
        hist = AnalyticsEngine.computeHistogram(SAMPLE_ROWS, ["ecm"], bins=2)
        self.assertEqual(hist.totalValues, 3)
        self.assertEqual(hist.min, 240.0)
        self.assertEqual(hist.max, 365.0)
        self.assertEqual(sum(b.count for b in hist.bins), 3)

        summary = AnalyticsEngine.computeSummary(
            SAMPLE_ROWS, ["process"], metricPath=["cross_section_pb"]
        )
        self.assertEqual(summary.totalEntries, 3)
        by_group = {g.group: g for g in summary.groups}
        self.assertEqual(by_group["ee_ZH"].count, 2)
        self.assertAlmostEqual(by_group["ee_ZH"].mean or 0.0, 0.1645, places=4)

        cmp = AnalyticsEngine.computeCompare(
            SAMPLE_ROWS[:2], SAMPLE_ROWS[2:], [["ecm"], ["cross_section_pb"]]
        )
        self.assertEqual(cmp.countA, 2)
        self.assertEqual(cmp.countB, 1)
        self.assertAlmostEqual(cmp.deltas[0].meanA or 0.0, 302.5, places=4)
        self.assertAlmostEqual(cmp.deltas[0].meanB or 0.0, 240.0, places=4)

        cov = AnalyticsEngine.computeCoverage(SAMPLE_ROWS, ["process"], ["ecm"])
        self.assertEqual(len(cov.cells), 3)

    def test_analytics_service_end_to_end(self) -> None:
        async def run() -> None:
            repo = FakeEntityRepository([SAMPLE_ROWS])
            svc = AnalyticsService(repo)  # type: ignore[arg-type]
            h = await svc.histogram(HistogramRequest(field={"ecm": {}}, bins=2))
            self.assertEqual(h.totalValues, 3)

            s = await svc.summary(
                SummaryRequest(groupBy={"campaign": {}}, metric={"ecm": {}})
            )
            self.assertEqual(len(s.groups), 2)

            c_repo = FakeEntityRepository([SAMPLE_ROWS[:2], SAMPLE_ROWS[2:]])
            c_svc = AnalyticsService(c_repo)  # type: ignore[arg-type]
            c = await c_svc.compare(
                CompareRequest(
                    groupA=EntityRequestModel(entry_type="collision"),
                    groupB=EntityRequestModel(entry_type="collision"),
                    metrics=[{"ecm": {}}],
                )
            )
            self.assertEqual(c.countA, 2)
            self.assertEqual(c.countB, 1)

            cov = await svc.coverage(row_field="process", col_field="ecm")
            self.assertEqual(len(cov.cells), 3)

        asyncio.run(run())


class TestExportModule(unittest.TestCase):
    def test_all_five_export_formatters(self) -> None:
        # CSV
        csv_text = ExportFormatters.render(ExportFormat.CSV, SAMPLE_ROWS)
        parsed_csv = list(csv.DictReader(io.StringIO(csv_text)))
        self.assertEqual(len(parsed_csv), 3)
        self.assertIn("metadata.ecm", parsed_csv[0])

        # JSON
        json_text = ExportFormatters.render(ExportFormat.JSON, SAMPLE_ROWS)
        parsed_json = json.loads(json_text)
        self.assertEqual(len(parsed_json), 3)

        # YAML
        yaml_text = ExportFormatters.render(ExportFormat.YAML, SAMPLE_ROWS)
        self.assertTrue(yaml_text.startswith("processList:"))
        self.assertIn("wzp6_ee_ZH_ecm240:", yaml_text)

        # TOML
        toml_text = ExportFormatters.render(ExportFormat.TOML, SAMPLE_ROWS)
        self.assertEqual(toml_text.count("[[entries]]"), 3)

        # Python dict literal (must parse cleanly with ast.parse)
        py_text = ExportFormatters.render(ExportFormat.PYTHON, SAMPLE_ROWS)
        tree = ast.parse(py_text)
        self.assertEqual(len(tree.body), 1)
        self.assertIn("wzp6_ee_ZH_ecm240", py_text)

    def test_export_service_applies_take_and_media_type(self) -> None:
        async def run() -> None:
            repo = FakeEntityRepository([SAMPLE_ROWS])
            svc = ExportService(repo)  # type: ignore[arg-type]
            payload, media_type, filename = await svc.export(
                EntityRequestModel(
                    entry_type="collision",
                    take={"name": {}, "ecm": {}},
                ),
                ExportFormat.JSON,
            )
            self.assertEqual(filename, "umb_export.json")
            self.assertIn("application/json", media_type)
            data = json.loads(payload)
            self.assertEqual(
                set(data[0]["metadata"].keys()),
                {"name", "ecm"},
            )

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
