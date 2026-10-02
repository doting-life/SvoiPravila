"""The curl examples must cover every Mini App operation in the committed
OpenAPI contract and must not document operations that do not exist."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURL_DOC = ROOT / "examples" / "curl" / "README.md"
OPENAPI = ROOT / "docs" / "openapi.json"

CURL_CALL = re.compile(r'curl -s -X (GET|POST|PUT|PATCH|DELETE) "\$API(/v1/miniapp/[^"]+)"')


def _template_to_regex(path: str) -> re.Pattern[str]:
    return re.compile("^" + re.sub(r"\\\{[^}]+\\\}", r"[^/]+", re.escape(path)) + "$")


def _operations() -> set[tuple[str, str]]:
    spec = json.loads(OPENAPI.read_text(encoding="utf-8"))
    return {
        (method.upper(), path)
        for path, item in spec["paths"].items()
        if path.startswith("/v1/miniapp/")
        for method in item
        if method in {"get", "post", "put", "patch", "delete"}
    }


def _documented_calls() -> list[tuple[str, str]]:
    return CURL_CALL.findall(CURL_DOC.read_text(encoding="utf-8"))


def test_curl_examples_cover_every_miniapp_operation() -> None:
    operations = _operations()
    calls = _documented_calls()
    covered: set[tuple[str, str]] = set()
    for method, url in calls:
        matches = {
            (op_method, template)
            for op_method, template in operations
            if op_method == method and _template_to_regex(template).match(url)
        }
        assert matches, f"curl example {method} {url} has no matching OpenAPI operation"
        covered |= matches
    assert covered == operations


def test_curl_examples_always_send_init_data_header() -> None:
    text = CURL_DOC.read_text(encoding="utf-8")
    for line in text.splitlines():
        if CURL_CALL.search(line):
            assert '-H "$H"' in line, line
    assert "user_id" not in text.replace("never send `user_id`", "")
