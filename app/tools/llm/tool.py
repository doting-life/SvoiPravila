from __future__ import annotations

from typing import Any

from app.artifacts import ARTIFACT_MODELS
from app.tools.base import BaseTool, ToolResult
from app.tools.llm.base import StructuredGenerationRequest, StructuredLLMProvider


class LLMGenerateTool(BaseTool):
    name = "llm_generate"
    capability = "structured_generation"

    def __init__(self, provider: StructuredLLMProvider) -> None:
        self.provider = provider

    async def execute(
        self,
        *,
        system_instructions: str,
        user_payload: dict[str, Any],
        output_artifact: str,
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        try:
            model = ARTIFACT_MODELS[output_artifact]
            response = await self.provider.generate(
                StructuredGenerationRequest(
                    system_instructions=system_instructions,
                    user_payload=user_payload,
                    output_model=model,
                    metadata=metadata or {},
                )
            )
            validated = model.model_validate(response.payload)
            return ToolResult(
                success=True,
                data=validated,
                metadata={
                    "provider": response.provider,
                    "model": response.model,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))
