from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ToolResult:
    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


class BaseTool(ABC):
    name: str
    capability: str

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        raise NotImplementedError
