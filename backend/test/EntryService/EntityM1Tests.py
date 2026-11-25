from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

from pydantic import ValidationError

from app.database.DatabaseInitializer import DatabaseInitializer
from app.engine.entry.EntityEngine import EntityEngine
from app.engine.entry.planner.SQLPlanner import SQLPlanner
from app.models.entity.EntityRoute import EntityRoute
from app.models.request.AggregateStatementModel import (
    AggregateFunction,
    AggregateStatementModel,
)
from app.models.request.EntityRequestModel import EntityRequestModel
from app.models.request.EntrySelectionStatementVersionsModel import (
    EntryRequestVersionsModel,
)
from app.models.request.GetStatementModel import GetStatementModel
from app.models.request.PaginationStatementModel import PaginationStatementModel
from app.models.request.SortStatementModel import (
    SortStatementModel,
    SortStatementOrder,
)
from app.models.request.where.expression.FieldExpression import (
    BooleanOperator,
    FieldExpression,
)
from app.models.request.where.unary.ListOperator import ListOperator
from app.models.request.where.unary.ListStatement import ListStatement
from app.models.request.where.unary.Operator import Operator
from app.models.request.where.unary.UnaryStatement import UnaryStatement
from app.models.request.where.unary.Value import Value
from app.services.entity.EntityRequestValidatorService import EntityRequestValidator
from app.services.entity.EntityService import EntityService
from app.utility.PathTreeToList import conditionTreeToList, pathTreeToList
from app.workers.FileWatcher import FileWatcher


class FakeRepository:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.calls: list[tuple[str, list[Any]]] = []

    async def executeQuery(
        self, sql: str, params: list[Any]
    ) -> list[dict[str, Any]]:
        self.calls.append((sql, params))
        return self.rows


class FakeConnection:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple[Any, ...]]] = []

    async def execute(self, sql: str, *args: Any) -> str:
        self.executed.append((sql, args))
        return "OK"

    @asynccontextmanager
    async def transaction(self) -> Any:
        yield


class TestPathTreeUtilities(unittest.TestCase):
    def test_path_tree_to_list_nested(self) -> None:
        tree = {"ecm": {}, "parent": {"generator": {"name": {}, "version": {}}}}
        paths = pathTreeToList(tree)
        self.assertEqual(
            paths,
            [["ecm"], ["parent", "generator", "name"], ["parent", "generator", "version"]],
        )

    def test_path_tree_rejects_non_dict_leaf(self) -> None:
        with self.assertRaises(TypeError):
            pathTreeToList({"ecm": "bad"})

    def test_condition_tree_to_list(self) -> None:
        tree = {"ecm": ">10", "parent": {"generator": {"version": "=8.3"}}}
        self.assertEqual(
            conditionTreeToList(tree),
            [(["ecm"], ">10"), (["parent", "generator", "version"], "=8.3")],
        )


class TestRequestModels(unittest.TestCase):
    def test_get_statement_defaults_none_and_single_mode(self) -> None:
        g = GetStatementModel(last=5)
        self.assertIsNone(g.first)
        self.assertEqual(g.last, 5)
        self.assertIsNone(g.random)
        self.assertIsNone(g.uniform)

        with self.assertRaises(ValidationError):
            GetStatementModel(first=2, last=3)

    def test_pagination_optional_cursor(self) -> None:
        p = PaginationStatementModel(size=10)
        self.assertEqual(p.size, 10)
        self.assertIsNone(p.cursor)

        with self.assertRaises(ValidationError):
            PaginationStatementModel(size=0)

    def test_entity_request_accepts_single_and_list_entry_type(self) -> None:
        r1 = EntityRequestModel(entry_type="collision", version=3)
        r2 = EntityRequestModel(entry_type=["collision", "beam_config"])
        self.assertEqual(r1.entry_type, "collision")
        self.assertEqual(r1.version, 3)
        self.assertEqual(r2.entry_type, ["collision", "beam_config"])


class TestSQLPlanner(unittest.TestCase):
    def test_contains_without_sort_and_pagination_placeholder_numbering(self) -> None:
        req = EntityRequestModel(
            entry_type="collision",
            contains={"campaign": {}},
            without={"simulation": {}},
            sort=SortStatementModel(by={"ecm": {}}, order=SortStatementOrder.DESC),
            page=PaginationStatementModel(
                size=10, cursor="00000000-0000-0000-0000-000000000001"
            ),
        )
        plan = SQLPlanner(req).generatePlan()

        # Must have sequential $1..$6 with zero collisions or leftover '?'
        self.assertNotIn("?", plan.sql)
        for i in range(1, 7):
            self.assertIn(f"${i}", plan.sql)
        self.assertEqual(len(plan.params), 6)
        self.assertIn("NOT jsonb_path_exists(metadata, $3)", plan.sql)
        self.assertIn("DESC NULLS LAST", plan.sql)
        self.assertIn("LIMIT $6", plan.sql)
        self.assertEqual(plan.params[-1], 11)  # size + 1

    def test_wildcard_where_and_list_operators(self) -> None:
        req = EntityRequestModel(where={"*": ">=302"})
        expr = FieldExpression(
            children=[
                UnaryStatement(operator=Operator.GREATEREQUAL, value=Value("302", 302)),
                ListStatement(
                    operator=ListOperator.NOTIN,
                    values=[Value("DIRAC", "DIRAC")],
                ),
            ],
            operators=[BooleanOperator.AND],
        )
        with patch(
            "app.engine.entry.planner.SQLPlanner.ExpressionHandler.generateExpression",
            return_value=expr,
        ):
            plan = SQLPlanner(req).generatePlan()

        self.assertIn("jsonb_path_exists(metadata, $1)", plan.sql)
        self.assertIn("NOT jsonb_path_exists(metadata, $2)", plan.sql)
        self.assertEqual(plan.params[0], "$.** ? (@ >= 302)")
        self.assertEqual(plan.params[1], '$.** ? (@ == "DIRAC")')

    def test_aggregate_plan(self) -> None:
        req = EntityRequestModel(
            entry_type="collision",
            aggregate=AggregateStatementModel(
                by={"parent": {"ecm": {}}}, fn=AggregateFunction.AVG
            ),
        )
        path, plan = SQLPlanner(req).generateAggregatePlan()
        self.assertEqual(path, ["parent", "ecm"])
        self.assertIn("AVG((jsonb_path_query_first(metadata, $1) #>> '{}')::double precision)", plan.sql)
        self.assertEqual(plan.params[0], '$.**."parent"."ecm"')
        self.assertEqual(plan.params[1], ["collision"])

    def test_distinct_plan(self) -> None:
        req = EntityRequestModel(distinct={"parent": {"generator": {"name": {}}}})
        path, plan = SQLPlanner(req).generateDistinctPlan()
        self.assertEqual(path, ["parent", "generator", "name"])
        self.assertIn("SELECT DISTINCT jsonb_path_query_first(metadata, $1)", plan.sql)
        self.assertIn("jsonb_path_exists(metadata, $2)", plan.sql)

    def test_versions_plan(self) -> None:
        req = EntityRequestModel(
            id="00000000-0000-0000-0000-000000000001",
            versions=EntryRequestVersionsModel(last=5, by="alice"),
        )
        plan = SQLPlanner(req).generateVersionsPlan()
        self.assertIn("ORDER BY version DESC LIMIT $3", plan.sql)
        self.assertEqual(plan.params, ["00000000-0000-0000-0000-000000000001", "alice", 5])


class TestEntityEngine(unittest.TestCase):
    def test_apply_get_clause_last_and_uniform(self) -> None:
        rows = [{"id": str(i)} for i in range(10)]
        last3 = EntityEngine(EntityRequestModel(get=GetStatementModel(last=3))).applyGetClause(rows)
        self.assertEqual([r["id"] for r in last3], ["7", "8", "9"])

        uniform3 = EntityEngine(EntityRequestModel(get=GetStatementModel(uniform=3))).applyGetClause(rows)
        self.assertEqual(len(uniform3), 3)

    def test_apply_take_clause_preserves_hierarchy(self) -> None:
        req = EntityRequestModel(
            take={"ecm": {}, "parent": {"generator": {"name": {}}}}
        )
        rows = [
            {
                "id": "u1",
                "metadata": {
                    "ecm": 13.6,
                    "secret": "drop-me",
                    "parent": {"generator": {"name": "Pythia", "version": "8.3"}},
                },
            }
        ]
        projected = EntityEngine(req).applyTakeClause(rows)
        self.assertEqual(
            projected[0]["metadata"],
            {"ecm": 13.6, "parent": {"generator": {"name": "Pythia"}}},
        )

    def test_apply_pagination_sets_has_more_and_cursor(self) -> None:
        req = EntityRequestModel(page=PaginationStatementModel(size=2))
        rows = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        pageRows, nextCursor, hasMore = EntityEngine(req).applyPagination(rows)
        self.assertEqual(len(pageRows), 2)
        self.assertEqual(nextCursor, "b")
        self.assertTrue(hasMore)


class TestValidatorAndService(unittest.TestCase):
    def test_validator_rules(self) -> None:
        # Empty request rejected
        self.assertFalse(EntityRequestValidator(EntityRequestModel()).validate().valid)

        # /search requires search clause
        res = EntityRequestValidator(
            EntityRequestModel(entry_type="collision"), route=EntityRoute.SEARCH
        ).validate()
        self.assertFalse(res.valid)

        # /stat requires stat clause
        res = EntityRequestValidator(
            EntityRequestModel(entry_type="collision"), route=EntityRoute.STAT
        ).validate()
        self.assertFalse(res.valid)

        # version + versions rejected
        res = EntityRequestValidator(
            EntityRequestModel(
                id="u1", version=2, versions=EntryRequestVersionsModel(last=2)
            )
        ).validate()
        self.assertFalse(res.valid)

    def test_service_routes_end_to_end(self) -> None:
        async def run() -> None:
            # STAT aggregate
            repo = FakeRepository([{"value": 13.6}])
            service = EntityService(route=EntityRoute.STAT, repository=repo)  # type: ignore[arg-type]
            resp = await service.response(
                EntityRequestModel(
                    aggregate=AggregateStatementModel(
                        by={"ecm": {}}, fn=AggregateFunction.AVG
                    )
                )
            )
            self.assertEqual(resp.status, "ok")
            self.assertIsNotNone(resp.aggregate)
            assert resp.aggregate is not None
            self.assertEqual(resp.aggregate.value, 13.6)

            # GET versions
            now = datetime.now(timezone.utc)
            vRepo = FakeRepository(
                [
                    {
                        "id": "u1",
                        "version": 2,
                        "created_at": now,
                        "created_by": "amir",
                        "source": "DIRAC",
                    }
                ]
            )
            vService = EntityService(route=EntityRoute.GET, repository=vRepo)  # type: ignore[arg-type]
            vResp = await vService.response(
                EntityRequestModel(id="u1", versions=EntryRequestVersionsModel(last=3))
            )
            self.assertEqual(vResp.returned, 1)
            assert vResp.versions is not None
            self.assertEqual(vResp.versions[0].version, 2)

            # RAND
            rRepo = FakeRepository([{"id": "u9", "metadata": {"ecm": 91.2}}])
            rService = EntityService(route=EntityRoute.RAND, repository=rRepo)  # type: ignore[arg-type]
            rResp = await rService.response(EntityRequestModel(), randLimit=1)
            self.assertEqual(rResp.returned, 1)
            self.assertIn("ORDER BY RANDOM() LIMIT $1", rRepo.calls[0][0])

        asyncio.run(run())


class TestDatabaseInitializerAndFileWatcher(unittest.TestCase):
    def test_db_initializer_preserves_tables_by_default(self) -> None:
        async def run() -> None:
            conn = FakeConnection()
            with tempfile.TemporaryDirectory() as tmp:
                schemaPath = Path(tmp) / "schema.sql"
                schemaPath.write_text("CREATE TABLE IF NOT EXISTS entries (id UUID);", encoding="utf-8")
                with patch("app.database.DatabaseInitializer.get_settings") as mockSettings:
                    mockSettings.return_value.databaseSchemaAdvisoryLock = 42
                    mockSettings.return_value.databaseSchemaPath = str(schemaPath)
                    await DatabaseInitializer(conn).initialize(reset=False)

            sqls = [s for s, _ in conn.executed]
            self.assertTrue(any("pg_advisory_lock" in s for s in sqls))
            self.assertTrue(any("pg_advisory_unlock" in s for s in sqls))
            self.assertFalse(any("DROP TABLE" in s for s in sqls))

        asyncio.run(run())

    def test_file_watcher_does_not_reingest_processed(self) -> None:
        async def run() -> None:
            conn = FakeConnection()
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                sample = root / "collision__DIRAC__amir.json"
                sample.write_text(json.dumps([{"ecm": 13.6, "uuid": "drop"}]), encoding="utf-8")

                watcher = FileWatcher(conn, root=root)
                await watcher._scan()
                firstCount = len(conn.executed)
                self.assertTrue((root / "processed" / sample.name).exists())
                self.assertGreater(firstCount, 0)

                # Second scan must NOT re-process files in processed/
                await watcher._scan()
                self.assertEqual(len(conn.executed), firstCount)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
