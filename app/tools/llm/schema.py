from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel


def output_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    """JSON Schema of an existing artifact model, passed unchanged to providers."""
    return model.model_json_schema()


def schema_name(model: type[BaseModel]) -> str:
    """Stable schema name derived from the Pydantic model class name."""
    return model.__name__


def user_input(payload: dict[str, Any]) -> str:
    """Serialize the stage payload exactly like the OpenAI provider does."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def parse_structured_json(raw: Any, model: type[BaseModel], provider: str) -> dict[str, Any]:
    """Parse a provider JSON string and validate it with the requested Pydantic model.

    Error messages never include the raw content, which may echo user text.
    """
    if not isinstance(raw, str) or not raw.strip():
        raise RuntimeError(f"{provider} returned no structured output")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{provider} returned malformed JSON structured output") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"{provider} structured output is not a JSON object")
    return model.model_validate(data).model_dump(mode="json")
