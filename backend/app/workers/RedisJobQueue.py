from __future__ import annotations

from collections import deque
from typing import Any, Protocol


class JobQueueProtocol(Protocol):
    """Reliable job queue contract supporting atomic claim, ack, and crash recovery."""

    async def enqueue(self, job_id: str) -> None: ...
    async def dequeue(self, *, timeout_s: int = 5) -> str | None: ...
    async def ack(self, job_id: str) -> None: ...
    async def recoverProcessing(self) -> list[str]: ...
    async def close(self) -> None: ...


class RedisJobQueue:
    """
    Reliable Redis-backed FIFO queue using LPUSH + BLMOVE (queue -> processing) + LREM.

    Because claimed job IDs live in `processing_key` until `ack()` is called,
    a worker crash or restart never loses in-flight jobs: calling
    `recoverProcessing()` on startup atomically returns stranded IDs to the main queue.
    """

    def __init__(
        self,
        client: Any,
        *,
        queue_key: str = "umb:jobs:queue",
        processing_key: str = "umb:jobs:processing",
    ) -> None:
        self._client = client
        self._queue_key = queue_key
        self._processing_key = processing_key

    @classmethod
    def fromUrl(
        cls,
        url: str,
        *,
        queue_key: str = "umb:jobs:queue",
        processing_key: str = "umb:jobs:processing",
    ) -> RedisJobQueue:
        import redis.asyncio as aioredis

        client = aioredis.from_url(url, decode_responses=True)
        return cls(client, queue_key=queue_key, processing_key=processing_key)

    async def enqueue(self, job_id: str) -> None:
        await self._client.lpush(self._queue_key, job_id)

    async def dequeue(self, *, timeout_s: int = 5) -> str | None:
        raw = await self._client.blmove(
            self._queue_key,
            self._processing_key,
            timeout_s,
            "RIGHT",
            "LEFT",
        )
        if raw is None:
            return None
        return raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)

    async def ack(self, job_id: str) -> None:
        await self._client.lrem(self._processing_key, 1, job_id)

    async def recoverProcessing(self) -> list[str]:
        """Move all stranded job IDs from processing back to queue on worker startup."""
        recovered: list[str] = []
        while True:
            raw = await self._client.lmove(
                self._processing_key,
                self._queue_key,
                "RIGHT",
                "LEFT",
            )
            if raw is None:
                break
            job_id = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
            recovered.append(job_id)
        return recovered

    async def close(self) -> None:
        await self._client.aclose()


class InMemoryJobQueue:
    """In-memory implementation of JobQueueProtocol with identical claim/ack/recovery semantics."""

    def __init__(self) -> None:
        self.pending: deque[str] = deque()
        self.processing: deque[str] = deque()

    async def enqueue(self, job_id: str) -> None:
        self.pending.appendleft(job_id)

    async def dequeue(self, *, timeout_s: int = 5) -> str | None:
        _ = timeout_s
        if not self.pending:
            return None
        job_id = self.pending.pop()
        self.processing.appendleft(job_id)
        return job_id

    async def ack(self, job_id: str) -> None:
        try:
            self.processing.remove(job_id)
        except ValueError:
            pass

    async def recoverProcessing(self) -> list[str]:
        recovered: list[str] = []
        while self.processing:
            job_id = self.processing.pop()
            self.pending.appendleft(job_id)
            recovered.append(job_id)
        return recovered

    async def close(self) -> None:
        return None
