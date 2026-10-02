from __future__ import annotations

from typing import Any

from app.tools.llm.base import (
    StructuredGenerationRequest,
    StructuredGenerationResponse,
    StructuredLLMProvider,
)
from app.tools.llm.schema import output_json_schema, parse_structured_json, schema_name, user_input

DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class DeepSeekStructuredLLMProvider(StructuredLLMProvider):
    """DeepSeek Responses API adapter with JSON Schema structured output.

    Request: ``text={"format": {"type": "json_schema", "name": ..., "schema": ...}}``.
    The returned text is parsed and validated with the requested Pydantic model.
    Uses the OpenAI-format SDK pointed at the DeepSeek base URL; the SDK import
    is lazy so the core can be imported without production dependencies.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = DEFAULT_DEEPSEEK_BASE_URL,
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
        client: Any | None = None,
    ) -> None:
        self.model = model
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is required when LLM_PROVIDER=deepseek")
        if client is not None:
            self.client = client
            self._owns_client = False
            return
        try:
            from openai import AsyncOpenAI
        except ModuleNotFoundError as exc:
            raise RuntimeError("openai package is required when LLM_PROVIDER=deepseek") from exc
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
            max_retries=max_retries,
        )
        self._owns_client = True

    def __repr__(self) -> str:
        return f"DeepSeekStructuredLLMProvider(model={self.model!r})"

    async def generate(self, request: StructuredGenerationRequest) -> StructuredGenerationResponse:
        try:
            response = await self.client.responses.create(
                model=self.model,
                instructions=request.system_instructions,
                input=user_input(request.user_payload),
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema_name(request.output_model),
                        "schema": output_json_schema(request.output_model),
                    }
                },
            )
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            suffix = f" with HTTP {status}" if status else f": {type(exc).__name__}"
            raise RuntimeError(f"DeepSeek request failed{suffix}") from exc

        payload = parse_structured_json(
            getattr(response, "output_text", None), request.output_model, "DeepSeek"
        )
        usage = getattr(response, "usage", None)
        return StructuredGenerationResponse(
            payload=payload,
            provider="deepseek",
            model=str(getattr(response, "model", None) or self.model),
            input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
            cost_usd=None,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.close()
