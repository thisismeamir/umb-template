from __future__ import annotations

import asyncio
import unittest
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.middleware.logging import RequestLoggingMiddleware
from app.api.middleware.timing import TimingMiddleware
from app.config import Settings
from app.engine.auth.TokenEngine import TokenEngine, TokenError
from app.models.auth.AuthModels import LoginRequest, RefreshRequest, UserPrincipal
from app.models.collections.CollectionModels import (
    CollectionCreate,
    CollectionUpdate,
    MembershipUpdate,
)
from app.models.jobs.JobModels import JobStatus, JobSubmitRequest, JobTaskType
from app.services.auth.AuthService import AuthService
from app.services.collections.CollectionService import CollectionService
from app.services.jobs.JobService import JobService
from app.workers.JobWorker import JobWorker
from app.workers.RedisJobQueue import InMemoryJobQueue


class InMemoryCollectionRepository:
    def __init__(self) -> None:
        self.items: dict[str, dict[str, Any]] = {}
        self.members: dict[str, list[str]] = {}
        self._seq = 0

    async def listAccessible(self, owner: str) -> list[dict[str, Any]]:
        out = []
        for cid, row in self.items.items():
            if row["owner"] == owner or row["is_public"]:
                copy = dict(row)
                copy["member_count"] = len(self.members.get(cid, []))
                out.append(copy)
        return out

    async def getById(self, collection_id: str) -> dict[str, Any] | None:
        return self.items.get(collection_id)

    async def getEntryIds(self, collection_id: str) -> list[str]:
        return list(self.members.get(collection_id, []))

    async def create(
        self, *, name: str, description: str, owner: str, is_public: bool
    ) -> dict[str, Any]:
        self._seq += 1
        cid = f"00000000-0000-0000-0000-{self._seq:012d}"
        now = datetime.now(timezone.utc)
        row = {
            "id": cid,
            "name": name,
            "description": description,
            "owner": owner,
            "is_public": is_public,
            "created_at": now,
            "updated_at": now,
        }
        self.items[cid] = row
        self.members[cid] = []
        return row

    async def update(
        self,
        collection_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        is_public: bool | None = None,
    ) -> dict[str, Any] | None:
        row = self.items.get(collection_id)
        if row is None:
            return None
        if name is not None:
            row["name"] = name
        if description is not None:
            row["description"] = description
        if is_public is not None:
            row["is_public"] = is_public
        row["updated_at"] = datetime.now(timezone.utc)
        return row

    async def delete(self, collection_id: str) -> bool:
        return self.items.pop(collection_id, None) is not None

    async def addEntries(
        self, collection_id: str, entry_ids: list[str], added_by: str
    ) -> int:
        _ = added_by
        cur = self.members.setdefault(collection_id, [])
        added = 0
        for eid in entry_ids:
            if eid not in cur:
                cur.append(eid)
                added += 1
        return added

    async def removeEntries(self, collection_id: str, entry_ids: list[str]) -> int:
        cur = self.members.setdefault(collection_id, [])
        before = len(cur)
        self.members[collection_id] = [e for e in cur if e not in set(entry_ids)]
        return before - len(self.members[collection_id])


class InMemoryJobRepository:
    def __init__(self) -> None:
        self.jobs: dict[str, dict[str, Any]] = {}
        self._seq = 0

    async def create(
        self, *, task_type: JobTaskType, owner: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        self._seq += 1
        jid = f"10000000-0000-0000-0000-{self._seq:012d}"
        now = datetime.now(timezone.utc)
        row = {
            "id": jid,
            "task_type": task_type.value,
            "status": JobStatus.PENDING.value,
            "owner": owner,
            "payload": payload,
            "result": None,
            "error": None,
            "created_at": now,
            "updated_at": now,
        }
        self.jobs[jid] = row
        return row

    async def getById(self, job_id: str) -> dict[str, Any] | None:
        return self.jobs.get(job_id)

    async def listByOwner(self, owner: str, *, limit: int = 50) -> list[dict[str, Any]]:
        return [j for j in self.jobs.values() if j["owner"] == owner][:limit]

    async def updateStatus(
        self,
        job_id: str,
        status: JobStatus,
        *,
        result: Any = None,
        error: str | None = None,
    ) -> None:
        row = self.jobs[job_id]
        row["status"] = status.value
        row["result"] = result
        row["error"] = error
        row["updated_at"] = datetime.now(timezone.utc)


class FakeEntityRepository:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    async def executeQuery(
        self, sql: str, params: list[Any]
    ) -> list[dict[str, Any]]:
        _ = (sql, params)
        return self.rows


class TestMiddleware(unittest.TestCase):
    def test_timing_and_logging_middleware_headers(self) -> None:
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)
        app.add_middleware(TimingMiddleware)

        @app.get("/ping")
        async def ping() -> dict[str, str]:
            return {"ok": "true"}

        client = TestClient(app)
        resp = client.get("/ping")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("x-process-time", resp.headers)
        self.assertTrue(resp.headers["x-process-time"].endswith("ms"))
        self.assertIn("x-request-id", resp.headers)


class TestAuthModule(unittest.TestCase):
    def test_token_encode_decode_and_tamper_rejection(self) -> None:
        eng = TokenEngine("super-secret-test-key")
        tok = eng.encode(
            subject="amir", roles=["reader", "admin"], token_type="access", ttl_seconds=60
        )
        payload = eng.decode(tok, expected_type="access")
        self.assertEqual(payload["sub"], "amir")

        with self.assertRaises(TokenError):
            eng.decode(tok, expected_type="refresh")

        with self.assertRaises(TokenError):
            eng.decode(tok + "tampered")

    def test_auth_service_toggleable_modes(self) -> None:
        disabled_svc = AuthService(Settings(authEnabled=False, authSecretKey="k1"))
        anon = disabled_svc.resolvePrincipal(None)
        self.assertEqual(anon.username, "anonymous")
        self.assertFalse(anon.authenticated)

        enabled_svc = AuthService(Settings(authEnabled=True, authSecretKey="k2"))
        with self.assertRaises(HTTPException) as ctx:
            enabled_svc.resolvePrincipal(None)
        self.assertEqual(ctx.exception.status_code, 401)

        tokens = enabled_svc.login(LoginRequest(username="admin", password="pw"))
        user = enabled_svc.resolvePrincipal(f"Bearer {tokens.accessToken}")
        self.assertEqual(user.username, "admin")
        self.assertIn("admin", user.roles)

        refreshed = enabled_svc.refresh(RefreshRequest(refreshToken=tokens.refreshToken))
        self.assertNotEqual(refreshed.accessToken, "")


class TestCollectionsModule(unittest.TestCase):
    def test_collection_crud_membership_and_access_control(self) -> None:
        async def run() -> None:
            repo = InMemoryCollectionRepository()
            svc = CollectionService(repo)  # type: ignore[arg-type]
            alice = UserPrincipal(username="alice", roles=["reader", "writer"])
            bob = UserPrincipal(username="bob", roles=["reader", "writer"])

            created = await svc.createCollection(
                CollectionCreate(name="FCC ZH Runs", description="240 GeV", isPublic=False),
                alice,
            )
            self.assertEqual(created.owner, "alice")

            with self.assertRaises(HTTPException) as ctx:
                await svc.getCollection(created.id, bob)
            self.assertEqual(ctx.exception.status_code, 403)

            mem = await svc.updateMembership(
                created.id,
                MembershipUpdate(add=["e1", "e2"], remove=[]),
                alice,
            )
            self.assertEqual(mem.added, 2)
            self.assertEqual(mem.entryIds, ["e1", "e2"])

            await svc.updateCollection(created.id, CollectionUpdate(isPublic=True), alice)
            bob_view = await svc.getCollection(created.id, bob)
            self.assertEqual(bob_view.memberCount, 2)

            with self.assertRaises(HTTPException) as del_ctx:
                await svc.deleteCollection(created.id, bob)
            self.assertEqual(del_ctx.exception.status_code, 403)

            deleted = await svc.deleteCollection(created.id, alice)
            self.assertTrue(deleted["deleted"])

        asyncio.run(run())


class TestJobsModule(unittest.TestCase):
    def test_job_submit_enqueue_worker_and_result_polling(self) -> None:
        async def run() -> None:
            job_repo = InMemoryJobRepository()
            entity_repo = FakeEntityRepository(
                [
                    {"id": "e1", "metadata": {"name": "zh_240", "ecm": 240.0}},
                    {"id": "e2", "metadata": {"name": "zh_365", "ecm": 365.0}},
                ]
            )
            queue = InMemoryJobQueue()
            svc = JobService(job_repo, queue)  # type: ignore[arg-type]
            worker = JobWorker(queue, job_repo, entity_repo)  # type: ignore[arg-type]
            alice = UserPrincipal(username="alice", roles=["reader", "writer"])

            # Submit enqueues pending job
            record = await svc.submit(
                JobSubmitRequest(
                    taskType=JobTaskType.EXPORT,
                    payload={"format": "csv", "query": {"entry_type": "collision"}},
                ),
                alice,
            )
            self.assertEqual(record.status, JobStatus.PENDING)

            # Worker consumes & completes job
            processed = await worker.processOnce()
            self.assertEqual(processed, record.id)

            res = await svc.getResult(record.id, alice)
            self.assertEqual(res.status, JobStatus.DONE)
            self.assertEqual(res.result["filename"], "umb_export.csv")
            self.assertIn("zh_240", res.result["content"])

            # Histogram job
            hist_rec = await svc.submit(
                JobSubmitRequest(
                    taskType=JobTaskType.ANALYTICS_HISTOGRAM,
                    payload={"field": {"ecm": {}}, "bins": 2},
                ),
                alice,
            )
            await worker.processOnce()
            hist_res = await svc.getResult(hist_rec.id, alice)
            self.assertEqual(hist_res.result["totalValues"], 2)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
