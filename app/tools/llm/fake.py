from __future__ import annotations

from typing import Any

from app.artifacts import DecodeResult, HelpSayResult, SoftenResult
from app.tools.llm.base import (
    StructuredGenerationRequest,
    StructuredGenerationResponse,
    StructuredLLMProvider,
)


class FakeStructuredLLMProvider(StructuredLLMProvider):
    """Deterministic provider used for local development and tests.

    It intentionally does not try to be clever. Its purpose is to validate the
    orchestration, contracts, retries, and API surfaces without external calls.
    """

    async def generate(self, request: StructuredGenerationRequest) -> StructuredGenerationResponse:
        source = str(request.user_payload["message_request"]["text"])
        request_id = request.user_payload["message_request"]["request_id"]
        output_model = request.output_model

        if output_model is SoftenResult:
            rewritten = self._soften(source)
            payload: dict[str, Any] = {
                "version": "1.0",
                "request_id": request_id,
                "original_intent": source,
                "rewritten_message": rewritten,
                "tone_applied": "calm_direct",
                "constraints_respected": ["preserve_meaning", "reduce_hostility"],
            }
        elif output_model is DecodeResult:
            payload = {
                "version": "1.0",
                "request_id": request_id,
                "literal_meaning": source,
                "probable_intent": "Возможное намерение зависит от контекста; это лишь вероятная интерпретация.",
                "emotional_tone": "неопределённый",
                "uncertainty": "Высокая: без дополнительного контекста нельзя уверенно установить мотив автора.",
                "alternative_interpretations": [
                    "Буквальное сообщение без скрытого подтекста.",
                    "Попытка обозначить недовольство или ожидание ответа.",
                ],
            }
        elif output_model is HelpSayResult:
            payload = {
                "version": "1.0",
                "request_id": request_id,
                "message": source.strip(),
                "tone": "direct_natural",
                "preserved_intent": source,
                "warnings": [],
            }
        else:
            raise ValueError(f"Unsupported fake output model: {output_model.__name__}")

        return StructuredGenerationResponse(
            payload=payload,
            provider="fake",
            model="fake-structured-v1",
            input_tokens=max(len(source) // 4, 1),
            output_tokens=max(len(str(payload)) // 4, 1),
            cost_usd=0.0,
        )

    @staticmethod
    def _soften(text: str) -> str:
        substitutions = {
            "ты опять": "мне важно обратить внимание, что снова",
            "Ты опять": "Мне важно обратить внимание, что снова",
            "ничего не сделал": "это осталось несделанным",
            "ничего не сделала": "это осталось несделанным",
            "всегда": "часто",
            "никогда": "редко",
        }
        result = text
        for old, new in substitutions.items():
            result = result.replace(old, new)
        return result.strip()
