"""Contract tests for the committed OpenAPI schema (docs/openapi.json).

FastAPI/Pydantic is the API source of truth. These tests make sure the
committed contract matches a fresh export and that the public Mini App
surface keeps its authentication and request-shape guarantees.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from app.api import miniapp as miniapp_module
from scripts.export_openapi import JSON_PATH, YAML_PATH, build_schema, render_json, render_yaml


ROOT = Path(__file__).resolve().parent.parent
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}

EXPECTED_MINIAPP_OPERATIONS: set[tuple[str, str]] = {
    ("post", "/v1/miniapp/auth"),
    ("get", "/v1/miniapp/bootstrap"),
    ("get", "/v1/miniapp/relationships"),
    ("post", "/v1/miniapp/relationships"),
    ("patch", "/v1/miniapp/relationships/{relationship_id}"),
    ("delete", "/v1/miniapp/relationships/{relationship_id}"),
    ("put", "/v1/miniapp/me/default-relationship/{relationship_id}"),
    ("post", "/v1/miniapp/relationships/{relationship_id}/rules"),
    ("put", "/v1/miniapp/relationships/{relationship_id}/rules/{rule_id}"),
    ("delete", "/v1/miniapp/relationships/{relationship_id}/rules/{rule_id}"),
    ("post", "/v1/miniapp/assist/{workflow}"),
}


@pytest.fixture(scope="module")
def committed() -> dict[str, Any]:
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def _miniapp_operations(schema: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (method, path): operation
        for path, item in schema["paths"].items()
        if path.startswith("/v1/miniapp/")
        for method, operation in item.items()
        if method in HTTP_METHODS
    }


def _resolve(schema: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    ref = node.get("$ref")
    if ref is None:
        return node
    name = ref.rsplit("/", 1)[-1]
    return schema["components"]["schemas"][name]


def test_committed_openapi_matches_fresh_export() -> None:
    fresh = build_schema()
    assert JSON_PATH.read_bytes().decode("utf-8") == render_json(fresh), (
        "docs/openapi.json is stale; run: python scripts/export_openapi.py"
    )
    assert YAML_PATH.read_bytes().decode("utf-8") == render_yaml(fresh), (
        "docs/openapi.yaml is stale; run: python scripts/export_openapi.py"
    )


def test_committed_openapi_is_deterministically_formatted() -> None:
    raw = JSON_PATH.read_bytes()
    assert b"\r\n" not in raw
    assert raw.endswith(b"\n")
    assert raw.decode("utf-8") == render_json(json.loads(raw))


def test_all_miniapp_operations_exist(committed: dict[str, Any]) -> None:
    assert set(_miniapp_operations(committed)) == EXPECTED_MINIAPP_OPERATIONS


def test_full_schema_keeps_internal_and_telegram_surfaces(committed: dict[str, Any]) -> None:
    for path in ("/v1/assist/soften", "/v1/assist/decode", "/v1/assist/help-say", "/v1/telegram/webhook"):
        assert path in committed["paths"]


@pytest.mark.parametrize("operation_key", sorted(EXPECTED_MINIAPP_OPERATIONS))
def test_miniapp_operation_declares_telegram_init_data_header(
    committed: dict[str, Any], operation_key: tuple[str, str]
) -> None:
    operation = _miniapp_operations(committed)[operation_key]
    headers = [
        parameter
        for parameter in operation.get("parameters", [])
        if parameter.get("in") == "header" and parameter.get("name") == "X-Telegram-Init-Data"
    ]
    assert len(headers) == 1, f"{operation_key} must declare X-Telegram-Init-Data"


def _collect_property_names(schema: dict[str, Any], node: dict[str, Any], seen: set[str]) -> set[str]:
    names: set[str] = set()
    ref = node.get("$ref")
    if ref is not None:
        if ref in seen:
            return names
        seen.add(ref)
        node = _resolve(schema, node)
    names.update(node.get("properties", {}).keys())
    for child in node.get("properties", {}).values():
        names |= _collect_property_names(schema, child, seen)
    for key in ("anyOf", "oneOf", "allOf"):
        for child in node.get(key, []):
            names |= _collect_property_names(schema, child, seen)
    if isinstance(node.get("items"), dict):
        names |= _collect_property_names(schema, node["items"], seen)
    return names


def test_no_miniapp_request_body_contains_user_id(committed: dict[str, Any]) -> None:
    for key, operation in _miniapp_operations(committed).items():
        body = operation.get("requestBody")
        if body is None:
            continue
        for media in body.get("content", {}).values():
            names = _collect_property_names(committed, media["schema"], set())
            assert "user_id" not in names, f"{key} request body must not accept user_id"
        for parameter in operation.get("parameters", []):
            assert parameter.get("name") != "user_id", f"{key} must not accept user_id"


def _forbid_models() -> list[type[BaseModel]]:
    models: list[type[BaseModel]] = []
    for value in vars(miniapp_module).values():
        if isinstance(value, type) and issubclass(value, BaseModel) and value is not BaseModel:
            if value.model_config.get("extra") == "forbid":
                models.append(value)
    return models


def test_miniapp_request_schemas_forbid_extra_properties(committed: dict[str, Any]) -> None:
    schemas = committed["components"]["schemas"]
    request_refs: set[str] = set()
    for operation in _miniapp_operations(committed).values():
        for media in operation.get("requestBody", {}).get("content", {}).values():
            ref = media["schema"].get("$ref")
            if ref:
                request_refs.add(ref.rsplit("/", 1)[-1])

    assert request_refs, "expected Mini App request body schemas"
    forbid_names = {model.__name__ for model in _forbid_models()}
    for name in request_refs:
        assert name in forbid_names, f"{name} is expected to use extra='forbid'"
        assert schemas[name].get("additionalProperties") is False, f"{name} must set additionalProperties: false"


def test_all_forbid_models_in_schema_set_additional_properties_false(committed: dict[str, Any]) -> None:
    schemas = committed["components"]["schemas"]
    for model in _forbid_models():
        if model.__name__ in schemas:
            assert schemas[model.__name__].get("additionalProperties") is False, model.__name__
