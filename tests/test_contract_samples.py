"""Contract tests for the committed sample payloads under docs/fixtures/.

Every fixture must validate against the Pydantic models that back the
Mini App API, and its top-level keys must match the committed OpenAPI
component schema so frontend mocks cannot drift from the contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from app.api.miniapp import BootstrapResponse, RelationshipView
from app.artifacts import DeliveryResponse, RelationshipRule
from app.artifacts.models import DecodeResult, HelpSayResult, SoftenResult
from scripts.export_openapi import JSON_PATH


ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT / "docs" / "fixtures"

MODEL_FIXTURES: dict[str, type[BaseModel]] = {
    "bootstrap_with_default.json": BootstrapResponse,
    "bootstrap_without_default.json": BootstrapResponse,
    "relationship.json": RelationshipView,
    "rule.json": RelationshipRule,
    "delivery_soften.json": DeliveryResponse,
    "delivery_decode.json": DeliveryResponse,
    "delivery_help_say.json": DeliveryResponse,
    "delivery_blocked.json": DeliveryResponse,
    "delivery_error.json": DeliveryResponse,
}

STRUCTURED_RESULT_MODELS: dict[str, type[BaseModel]] = {
    "soften": SoftenResult,
    "decode": DecodeResult,
    "help-say": HelpSayResult,
}

ERROR_FIXTURES = ["error_401.json", "error_404.json", "error_503.json"]


def _load(name: str) -> Any:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def openapi() -> dict[str, Any]:
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def test_every_fixture_is_covered() -> None:
    on_disk = {path.name for path in FIXTURES_DIR.glob("*.json")}
    assert on_disk == set(MODEL_FIXTURES) | set(ERROR_FIXTURES)


@pytest.mark.parametrize("name", sorted(MODEL_FIXTURES))
def test_fixture_validates_against_model(name: str) -> None:
    model = MODEL_FIXTURES[name]
    payload = _load(name)
    parsed = model.model_validate(payload)
    assert parsed.model_dump(mode="json") == payload


@pytest.mark.parametrize("name", sorted(MODEL_FIXTURES))
def test_fixture_keys_match_openapi_component(name: str, openapi: dict[str, Any]) -> None:
    component = MODEL_FIXTURES[name].__name__
    schemas = openapi["components"]["schemas"]
    assert component in schemas, f"{component} missing from committed OpenAPI"
    properties = set(schemas[component].get("properties", {}))
    required = set(schemas[component].get("required", []))
    keys = set(_load(name))
    assert keys <= properties
    assert required <= keys


@pytest.mark.parametrize(
    "name",
    sorted(n for n in MODEL_FIXTURES if MODEL_FIXTURES[n] is DeliveryResponse),
)
def test_delivery_structured_result_matches_workflow(name: str) -> None:
    payload = _load(name)
    result = payload["structured_result"]
    if payload["status"] == "ok":
        assert result is not None
        parsed = STRUCTURED_RESULT_MODELS[payload["workflow"]].model_validate(result)
        assert str(parsed.request_id) == payload["request_id"]
    else:
        assert result is None


def test_bootstrap_default_relationship_is_owned() -> None:
    payload = _load("bootstrap_with_default.json")
    ids = {rel["relationship_id"] for rel in payload["relationships"]}
    assert payload["user"]["default_relationship_id"] in ids

    empty = _load("bootstrap_without_default.json")
    assert empty["user"]["default_relationship_id"] is None
    assert empty["relationships"] == []


@pytest.mark.parametrize("name", ERROR_FIXTURES)
def test_error_fixture_shape(name: str) -> None:
    payload = _load(name)
    assert set(payload) == {"detail"}
    assert isinstance(payload["detail"], str) and payload["detail"]
