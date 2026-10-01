from __future__ import annotations

from typing import Any
from uuid import UUID

from app.checkpoints.base import CheckpointSnapshot, CheckpointStore


class RedisCheckpointStore(CheckpointStore):
    """Redis-backed transient workflow checkpoint store.

    The concrete redis client is intentionally duck-typed so importing the core
    does not require the optional Redis runtime unless this adapter is selected.
    """

    def __init__(self, redis: Any, ttl_seconds: int = 1200) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    def _key(self, request_id: UUID) -> str:
        return f"request:{request_id}"

    async def save(self, snapshot: CheckpointSnapshot) -> None:
        await self.redis.set(
            self._key(snapshot.request_id),
            snapshot.model_dump_json(),
            ex=self.ttl_seconds,
        )

    async def load(self, request_id: UUID) -> CheckpointSnapshot | None:
        raw = await self.redis.get(self._key(request_id))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return CheckpointSnapshot.model_validate_json(raw)

    async def delete(self, request_id: UUID) -> None:
        await self.redis.delete(self._key(request_id))
