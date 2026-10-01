from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


@dataclass(slots=True)
class StructuredGenerationRequest:
    system_instructions: str
    user_payload: dict[str, Any]
    output_model: type[BaseModel]
    metadata: dict[str, Any]


@dataclass(slots=True)
class StructuredGenerationResponse:
    payload: dict[str, Any]
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float | None = None


class StructuredLLMProvider(ABC):
    @abstractmethod
    async def generate(self, request: StructuredGenerationRequest) -> StructuredGenerationResponse:
        raise NotImplementedError
