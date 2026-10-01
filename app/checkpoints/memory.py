from __future__ import annotations

from copy import deepcopy
from uuid import UUID

from app.checkpoints.base import CheckpointSnapshot, CheckpointStore


class InMemoryCheckpointStore(CheckpointStore):
    def __init__(self) -> None:
        self._items: dict[UUID, CheckpointSnapshot] = {}

    async def save(self, snapshot: CheckpointSnapshot) -> None:
        self._items[snapshot.request_id] = deepcopy(snapshot)

    async def load(self, request_id: UUID) -> CheckpointSnapshot | None:
        value = self._items.get(request_id)
        return deepcopy(value) if value else None

    async def delete(self, request_id: UUID) -> None:
        self._items.pop(request_id, None)
