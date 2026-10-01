from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.artifacts import Artifact


class WorkflowState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    request_id: UUID
    workflow: str
    artifacts: dict[str, Artifact] = Field(default_factory=dict)
    stage_attempts: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def put(self, name: str, artifact: Artifact) -> None:
        if artifact.request_id != self.request_id:
            raise ValueError(
                f"Artifact request_id mismatch: state={self.request_id}, artifact={artifact.request_id}"
            )
        self.artifacts[name] = artifact

    def require(self, names: list[str]) -> dict[str, Artifact]:
        missing = [name for name in names if name not in self.artifacts]
        if missing:
            raise KeyError(f"Missing required artifacts: {missing}")
        return {name: self.artifacts[name] for name in names}
