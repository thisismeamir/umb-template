from __future__ import annotations

import asyncio
import logging
import signal

from app.api.dependencies import Provider
from app.config import get_settings
from app.models.jobs.JobModels import JobStatus, JobTaskType
from app.repositories.entry.EntityRepository import EntityRepository
from app.repositories.jobs.JobRepository import JobRepository
from app.workers.JobRegistry import JobRegistry
from app.workers.RedisJobQueue import JobQueueProtocol, RedisJobQueue

logger = logging.getLogger("umb.worker")


class JobWorker:
    """
    Standalone async worker consuming job IDs from RedisJobQueue and persisting
    status/results into PostgreSQL so long-running jobs survive restarts.
    """

    def __init__(
        self,
        queue: JobQueueProtocol,
        job_repository: JobRepository,
        entity_repository: EntityRepository,
    ) -> None:
        self._queue = queue
        self._jobs = job_repository
        self._entities = entity_repository
        self._stopping = False

    def requestStop(self) -> None:
        self._stopping = True

    async def recoverOrphaned(self) -> list[str]:
        """Requeue any in-flight jobs left in Redis processing after an unclean exit."""
        recovered = await self._queue.recoverProcessing()
        for job_id in recovered:
            await self._jobs.updateStatus(job_id, JobStatus.PENDING)
            logger.warning("Recovered orphaned job_id=%s back to pending", job_id)
        return recovered

    async def processOnce(self, *, timeout_s: int = 5) -> str | None:
        """Claim one job from the queue, execute it, persist result/error, and ack."""
        job_id = await self._queue.dequeue(timeout_s=timeout_s)
        if job_id is None:
            return None

        row = await self._jobs.getById(job_id)
        if row is None:
            logger.warning("Skipping missing job_id=%s", job_id)
            await self._queue.ack(job_id)
            return job_id

        task_type = JobTaskType(row["task_type"])
        payload = row.get("payload") or {}

        await self._jobs.updateStatus(job_id, JobStatus.RUNNING)
        try:
            handler = JobRegistry.get(task_type)
            result = await handler(payload, self._entities)
            await self._jobs.updateStatus(job_id, JobStatus.DONE, result=result)
            logger.info("Completed job_id=%s task_type=%s", job_id, task_type.value)
        except Exception as exc:
            await self._jobs.updateStatus(
                job_id, JobStatus.FAILED, error=str(exc)
            )
            logger.exception("Failed job_id=%s task_type=%s", job_id, task_type.value)
        finally:
            await self._queue.ack(job_id)

        return job_id

    async def runForever(self, *, poll_timeout_s: int = 5) -> None:
        """Run recovery then poll Redis until stop is requested."""
        await self.recoverOrphaned()
        while not self._stopping:
            await self.processOnce(timeout_s=poll_timeout_s)


async def _main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    pool = await Provider.initPool()
    queue = RedisJobQueue.fromUrl(
        settings.broker_url,
        queue_key=settings.workerQueueName,
        processing_key=settings.workerProcessingQueueName,
    )

    async with pool.acquire() as conn:
        worker = JobWorker(
            queue=queue,
            job_repository=JobRepository(conn),
            entity_repository=EntityRepository(conn),
        )
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, worker.requestStop)
            except NotImplementedError:
                pass

        try:
            await worker.runForever(poll_timeout_s=settings.workerPollTimeoutSeconds)
        finally:
            await queue.close()
            await Provider.closePool()


if __name__ == "__main__":
    asyncio.run(_main())
