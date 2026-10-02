"""Export the FastAPI OpenAPI schema to docs/openapi.json and docs/openapi.yaml.

The schema is produced by ``app.openapi()`` only; application startup/shutdown
(lifespan) hooks are never executed, so no settings, databases or external
providers are required.

Usage:
    python scripts/export_openapi.py          # write files
    python scripts/export_openapi.py --check  # exit 1 if committed files differ
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

JSON_PATH = ROOT / "docs" / "openapi.json"
YAML_PATH = ROOT / "docs" / "openapi.yaml"


def build_schema() -> dict[str, Any]:
    from app.main import app

    return app.openapi()


def render_json(schema: dict[str, Any]) -> str:
    return json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def render_yaml(schema: dict[str, Any]) -> str:
    return yaml.safe_dump(schema, sort_keys=True, allow_unicode=True, default_flow_style=False, width=1000)


def render_all() -> dict[Path, str]:
    schema = build_schema()
    return {JSON_PATH: render_json(schema), YAML_PATH: render_yaml(schema)}


def _read(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_bytes().decode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if committed files differ from a fresh export")
    args = parser.parse_args(argv)

    outputs = render_all()
    if args.check:
        stale = [path for path, content in outputs.items() if _read(path) != content]
        for path in stale:
            print(f"OpenAPI contract out of date: {path.relative_to(ROOT).as_posix()}", file=sys.stderr)
        if stale:
            print("Run: python scripts/export_openapi.py", file=sys.stderr)
            return 1
        print("OpenAPI contract is up to date.")
        return 0

    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf-8"))
        print(f"Wrote {path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
