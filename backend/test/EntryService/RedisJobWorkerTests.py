from __future__ import annotations

import asyncio
import unittest
from collections import deque
from typing import Any

from app.models.auth.AuthModels import UserPrincipal
from app.models.jobs.JobModels import JobStatus, JobSubmitRequest, JobTaskType
from app.services.jobs.JobService import JobService
from app.workers.JobWorker import JobWorker
from app.workers.RedisJobQueue import InMemoryJobQueue, RedisJobQueue
from test.EntryService.EntityM3Tests import (
    FakeEntityRepository,
    InMemoryJobRepository,
)


class FakeAsyncRedisClient:
    """Minimal in-memory fake matching redis.asyncio LPUSH/BLMOVE/LMOVE/LREM."""

    def __init__(self) -> None:
        self.lists: dict[str, deque[str]] = {}
        self.closed = False

    def _list(self, key: str) -> deque[str]:
        return self.lists.setdefault(key, deque())

    async def lpush(self, key: str, value: str) -> int:
        lst = self._list(key)
        lst.appendleft(value)
        return len(lst)

    async def blmove(
        self, src: str, dst: str, timeout: int, src_side: str, dst_side: str
    ) -> str | None:
        _ = timeout
        return await self.lmove(src, dst, src_side, dst_side)

    async def lmove(
        self, src: str, dst: str, src_side: str, dst_side: str
    ) -> str | None:
        s = self._list(src)
        if not s:
            return None
        val = s.pop() if src_side == "RIGHT" else s.popleft()
        d = self._list(dst)
        if dst_side == "LEFT":
            d.appendleft(val)
        else:
            d.append(val)
        return val

    async def lrem(self, key: str, count: int, value: str) -> int:
        _ = count
        lst = self._list(key)
        try:
            lst.remove(value)
            return 1
        except ValueError:
            return 0

    async def aclose(self) -> None:
        self.closed = True


class TestRedisJobQueueAndWorker(unittest.TestCase):
    def test_redis_queue_claim_ack_and_crash_recovery(self) -> None:
        async def run() -> None:
            fake_redis = FakeAsyncRedisClient()
            queue = RedisJobQueue(
                fake_redis,
                queue_key="test:queue",
                processing_key="test:processing",
            )
            await queue.enqueue("job-1")
            await queue.enqueue("job-2")

            # Claim job-1 -> moves atomically to processing list
            claimed = await queue.dequeue(timeout_s=1)
            self.assertEqual(claimed, "job-1")
            self.assertEqual(list(fake_redis.lists["test:processing"]), ["job-1"])

            # Simulate worker crash before ack(): recoverProcessing returns job-1 to queue
            recovered = await queue.recoverProcessing()
            self.assertEqual(recovered, ["job-1"])
            self.assertEqual(list(fake_redis.lists["test:processing"]), [])

            # Re-claim and ack cleanly
            reclaimed = await queue.dequeue(timeout_s=1)
            self.assertEqual(reclaimed, "job-2")
            await queue.ack("job-2")
            self.assertEqual(list(fake_redis.lists["test:processing"]), [])

            await queue.close()
            self.assertTrue(fake_redis.closed)

        asyncio.run(run())

    def test_worker_survives_restart_and_recovers_orphaned_job(self) -> None:
        async def run() -> None:
            fake_redis = FakeAsyncRedisClient()
            queue = RedisJobQueue(fake_redis)
            job_repo = InMemoryJobRepository()
            entity_repo = FakeEntityRepository(
                [{"id": "e1", "metadata": {"name": "zh_240", "ecm": 240.0}}]
            )
            svc = JobService(job_repo, queue)  # type: ignore[arg-type]
            alice = UserPrincipal(username="alice", roles=["reader", "writer"])

            # 1. API submits job
            rec = await svc.submit(
                JobSubmitRequest(
                    taskType=JobTaskType.EXPORT,
                    payload={"format": "json", "query": {"entry_type": "collision"}},
                ),
                alice,
            )

            # 2. Worker #1 claims job and crashes mid-flight (never calls ack)
            claimed = await queue.dequeue(timeout_s=1)
            self.assertEqual(claimed, rec.id)
            await job_repo.updateStatus(rec.id, JobStatus.RUNNING)

            # 3. Worker #2 boots up, recovers orphaned job, and completes it
            worker2 = JobWorker(queue, job_repo, entity_repo)  # type: ignore[arg-type]
            recovered = await worker2.recoverOrphaned()
            self.assertEqual(recovered, [rec.id])
            self.assertEqual((await svc.getStatus(rec.id, alice)).status, JobStatus.PENDING)

            processed = await worker2.processOnce(timeout_s=1)
            self.assertEqual(processed, rec.id)

            final = await svc.getResult(rec.id, alice)
            self.assertEqual(final.status, JobStatus.DONE)
            self.assertIn("zh_240", final.result["content"])

        asyncio.run(run())

    def test_worker_marks_failed_and_acks_bad_payload(self) -> None:
        async def run() -> None:
            queue = InMemoryJobQueue()
            job_repo = InMemoryJobRepository()
            entity_repo = FakeEntityRepository([])
            svc = JobService(job_repo, queue)  # type: ignore[arg-type]
            worker = JobWorker(queue, job_repo, entity_repo)  # type: ignore[arg-type]
            alice = UserPrincipal(username="alice", roles=["reader", "writer"])

            # Invalid histogram payload (missing required 'field')
            rec = await svc.submit(
                JobSubmitRequest(
                    taskType=JobTaskType.ANALYTICS_HISTOGRAM,
                    payload={"bins": 5},
                ),
                alice,
            )
            await worker.processOnce()

            res = await svc.getResult(rec.id, alice)
            self.assertEqual(res.status, JobStatus.FAILED)
            self.assertIsNotNone(res.error)
            # Must be ack'd out of processing so it does not poison-loop on restart
            self.assertEqual(len(queue.processing), 0)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
