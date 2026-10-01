from __future__ import annotations

import json
from typing import Any

from app.tools.llm.base import (
    StructuredGenerationRequest,
    StructuredGenerationResponse,
    StructuredLLMProvider,
)


class OpenAIStructuredLLMProvider(StructuredLLMProvider):
    """OpenAI Responses API adapter using SDK-native Pydantic Structured Outputs.

    The SDK import is lazy so the domain/core can be imported in environments
    that do not install production-only dependencies.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
        client: Any | None = None,
    ) -> None:
        self.model = model
        if client is not None:
            self.client = client
            self._owns_client = False
            return
        try:
            from openai import AsyncOpenAI
        except ModuleNotFoundError as exc:
            raise RuntimeError("openai package is required when LLM_PROVIDER=openai") from exc
        self.client = AsyncOpenAI(
            api_key=api_key,
            timeout=timeout_seconds,
            max_retries=max_retries,
        )
        self._owns_client = True

    async def generate(self, request: StructuredGenerationRequest) -> StructuredGenerationResponse:
        response = await self.client.responses.parse(
            model=self.model,
            instructions=request.system_instructions,
            input=json.dumps(request.user_payload, ensure_ascii=False, separators=(",", ":")),
            text_format=request.output_model,
        )

        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("OpenAI returned no parsed structured output")

        usage = getattr(response, "usage", None)
        input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0)

        return StructuredGenerationResponse(
            payload=parsed.model_dump(mode="json"),
            provider="openai",
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=None,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.close()
