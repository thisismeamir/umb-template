from __future__ import annotations

import asyncio
import json
import unittest
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import Provider
from app.api.middleware.logging import RequestLoggingMiddleware
from app.api.middleware.timing import TimingMiddleware
from app.api.v1.router import ApiV1
from app.config import Settings
from app.services.auth.AuthService import AuthService
from app.workers.JobWorker import JobWorker
from app.workers.RedisJobQueue import InMemoryJobQueue
from test.EntryService.EntityM2Tests import (
    FakeNavigationRepository,
    SAMPLE_ROWS,
)
from test.EntryService.EntityM3Tests import (
    InMemoryCollectionRepository,
    InMemoryJobRepository,
)


class StubEntityRepository:
    """In-memory stub returning sample physics metadata rows for HTTP route testing."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    async def executeQuery(
        self, sql: str, params: list[Any]
    ) -> list[dict[str, Any]]:
        _ = params
        if "SELECT COUNT(*) AS count" in sql:
            return [{"count": len(self.rows)}]
        if any(fn in sql for fn in ("SELECT AVG(", "SELECT SUM(", "SELECT MIN(", "SELECT MAX(")):
            return [{"value": 281.67}]
        if "SELECT DISTINCT jsonb_path_query_first" in sql:
            return [{"value": "Whizard"}, {"value": "Pythia8"}]
        if "SELECT DISTINCT val #>> '{}' AS value" in sql:
            return [{"value": "winter2023"}, {"value": "spring2024"}]
        return self.rows


def _buildTestHarness(
    *, auth_enabled: bool = False
) -> tuple[TestClient, JobWorker]:
    v1 = ApiV1()
    subapp = v1.as_subapp()
    assert isinstance(subapp, FastAPI)

    subapp.add_middleware(RequestLoggingMiddleware)
    subapp.add_middleware(TimingMiddleware)

    entity_repo = StubEntityRepository(SAMPLE_ROWS)
    nav_repo = FakeNavigationRepository(
        values=[{"name": "winter2023", "count": 2, "entry_types": ["collision"]}],
        fields=[
            {
                "entry_type": "collision",
                "key": "ecm",
                "value_type": "float",
                "source": "DIRAC",
            }
        ],
    )
    coll_repo = InMemoryCollectionRepository()
    job_repo = InMemoryJobRepository()
    job_queue = InMemoryJobQueue()
    auth_svc = AuthService(
        Settings(authEnabled=auth_enabled, authSecretKey="integration-test-secret")
    )

    async def _ov_entity() -> StubEntityRepository:
        return entity_repo

    async def _ov_nav() -> FakeNavigationRepository:
        return nav_repo

    async def _ov_coll() -> InMemoryCollectionRepository:
        return coll_repo

    async def _ov_job() -> InMemoryJobRepository:
        return job_repo

    async def _ov_queue() -> InMemoryJobQueue:
        return job_queue

    async def _ov_auth() -> AuthService:
        return auth_svc

    subapp.dependency_overrides[Provider.entryRepository] = _ov_entity
    subapp.dependency_overrides[Provider.navigationRepository] = _ov_nav
    subapp.dependency_overrides[Provider.collectionRepository] = _ov_coll
    subapp.dependency_overrides[Provider.jobRepository] = _ov_job
    subapp.dependency_overrides[Provider.jobQueue] = _ov_queue
    subapp.dependency_overrides[Provider.authService] = _ov_auth

    worker = JobWorker(job_queue, job_repo, entity_repo)  # type: ignore[arg-type]
    return TestClient(subapp), worker


class TestApiV1Integration(unittest.TestCase):
    def test_health_and_middleware_headers(self) -> None:
        client, _ = _buildTestHarness()
        resp = client.get("/check/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")
        self.assertIn("x-process-time", resp.headers)
        self.assertIn("x-request-id", resp.headers)

    def test_entities_routes(self) -> None:
        client, _ = _buildTestHarness()
        r = client.post("/entity/", json={"entry_type": "collision", "take": {"name": {}, "ecm": {}}})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["returned"], 3)
        self.assertEqual(set(body["entities"][0]["metadata"].keys()), {"name", "ecm"})

        r_stat = client.post(
            "/entity/stat",
            json={"aggregate": {"by": {"ecm": {}}, "fn": "avg"}},
        )
        self.assertEqual(r_stat.status_code, 200)
        self.assertAlmostEqual(r_stat.json()["aggregate"]["value"], 281.67, places=2)

        r_rand = client.get("/entity/rand?n=1")
        self.assertEqual(r_rand.status_code, 200)

    def test_navigation_and_search_routes(self) -> None:
        client, _ = _buildTestHarness()
        r_nav = client.get("/navigation/campaigns")
        self.assertEqual(r_nav.status_code, 200)
        self.assertEqual(r_nav.json()["items"][0]["name"], "winter2023")

        r_fields = client.get("/navigation/fields")
        self.assertEqual(r_fields.status_code, 200)
        self.assertEqual(r_fields.json()["fields"][0]["key"], "ecm")

        r_search = client.get("/search/?q=Whizard")
        self.assertEqual(r_search.status_code, 200)
        self.assertEqual(r_search.json()["total"], 2)

        r_suggest = client.get("/search/suggest?field=campaign&prefix=win")
        self.assertEqual(r_suggest.status_code, 200)
        self.assertEqual(r_suggest.json()["suggestions"], ["winter2023"])

    def test_analytics_and_export_routes(self) -> None:
        client, _ = _buildTestHarness()
        r_hist = client.post("/analytics/histogram", json={"field": {"ecm": {}}, "bins": 2})
        self.assertEqual(r_hist.status_code, 200)
        self.assertEqual(r_hist.json()["totalValues"], 3)

        r_cov = client.get("/analytics/coverage?row_field=process&col_field=ecm")
        self.assertEqual(r_cov.status_code, 200)
        self.assertEqual(len(r_cov.json()["cells"]), 3)

        for fmt, expected_ct in [
            ("csv", "text/csv"),
            ("json", "application/json"),
            ("yaml", "application/x-yaml"),
            ("toml", "application/toml"),
            ("python", "text/x-python"),
        ]:
            r_exp = client.post(f"/export/{fmt}", json={"entry_type": "collision"})
            self.assertEqual(r_exp.status_code, 200)
            self.assertIn(expected_ct, r_exp.headers["content-type"])
            self.assertIn("attachment; filename=", r_exp.headers["content-disposition"])

    def test_auth_collections_and_jobs_flow(self) -> None:
        client, worker = _buildTestHarness(auth_enabled=True)

        self.assertEqual(client.get("/collections/").status_code, 401)

        login = client.post("/auth/login", json={"username": "amir", "password": "secret"})
        self.assertEqual(login.status_code, 200)
        token = login.json()["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/auth/me", headers=headers)
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["user"]["username"], "amir")

        created = client.post(
            "/collections/",
            json={"name": "FCC ZH", "description": "240 GeV", "isPublic": False},
            headers=headers,
        )
        self.assertEqual(created.status_code, 200)
        cid = created.json()["id"]

        mem = client.post(
            f"/collections/{cid}/events",
            json={"add": ["00000000-0000-0000-0000-000000000001"], "remove": []},
            headers=headers,
        )
        self.assertEqual(mem.status_code, 200)
        self.assertEqual(mem.json()["added"], 1)

        # Submit job -> pending in DB & queued in Redis
        job = client.post(
            "/jobs/",
            json={
                "taskType": "export",
                "payload": {"format": "json", "query": {"entry_type": "collision"}},
            },
            headers=headers,
        )
        self.assertEqual(job.status_code, 200)
        self.assertEqual(job.json()["status"], "pending")
        jid = job.json()["id"]

        # Worker executes queued job independently of HTTP request lifecycle
        asyncio.run(worker.processOnce())

        res = client.get(f"/jobs/{jid}/result", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "done")
        self.assertEqual(len(json.loads(res.json()["result"]["content"])), 3)


if __name__ == "__main__":
    unittest.main()
