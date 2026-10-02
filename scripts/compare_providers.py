"""Provider comparison harness (developer tool, not a production subsystem).

Runs the SAME eval cases through the real WorkflowEngine (build_container) with
each selected LLM provider and records, per case:

    provider, model, workflow, case_id, success, latency_ms, schema_valid,
    status, error, result

No subjective scoring and no "winner". Secrets are read from the environment /
.env exactly like the app does and are never written to the report.

Usage:
    python -m scripts.compare_providers --providers fake
    python -m scripts.compare_providers --providers openai,gigachat,deepseek \
        --cases evals/cases --output evals/results/run.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.artifacts import ARTIFACT_MODELS  # noqa: E402
from app.artifacts.models import AssistRequest, WorkflowName  # noqa: E402
from app.container import build_container  # noqa: E402
from app.settings import AppSettings  # noqa: E402

DEFAULT_CASES_DIR = ROOT / "evals" / "cases"
PROVIDERS = ("fake", "openai", "gigachat", "deepseek")
RESULT_ARTIFACT = {
    WorkflowName.SOFTEN: "soften_result",
    WorkflowName.DECODE: "decode_result",
    WorkflowName.HELP_SAY: "help_say_result",
}


@dataclass(slots=True)
class EvalCase:
    case_id: str
    workflow: WorkflowName
    text: str
    language: str = "ru"
    relationship_id: str | None = None
    notes: str = ""


@dataclass(slots=True)
class EvalRecord:
    provider: str
    model: str | None
    workflow: str
    case_id: str
    success: bool
    latency_ms: float
    schema_valid: bool
    status: str | None = None
    error: str | None = None
    result: dict[str, Any] | None = field(default=None)


def load_cases(path: Path) -> list[EvalCase]:
    files = sorted(path.glob("*.json")) if path.is_dir() else [path]
    cases: list[EvalCase] = []
    for file in files:
        for raw in json.loads(file.read_text(encoding="utf-8")):
            cases.append(
                EvalCase(
                    case_id=raw["case_id"],
                    workflow=WorkflowName(raw["workflow"]),
                    text=raw["text"],
                    language=raw.get("language", "ru"),
                    relationship_id=raw.get("relationship_id"),
                    notes=raw.get("notes", ""),
                )
            )
    return cases


def settings_for(provider: str, base: AppSettings | None = None) -> AppSettings:
    """Same settings as the app, with only LLM_PROVIDER switched and in-memory storage."""
    base = base or AppSettings()
    data = base.model_dump()
    data.update(
        llm_provider=provider,
        relationship_backend="memory",
        checkpoint_backend="memory",
        telegram_enabled=False,
    )
    return AppSettings.model_validate(data)


async def run_case(provider: str, case: EvalCase, settings: AppSettings) -> EvalRecord:
    container = build_container(settings)
    started = time.perf_counter()
    try:
        response = await container.engine.execute(
            case.workflow,
            AssistRequest(
                user_id="u-1",
                text=case.text,
                relationship_id=case.relationship_id,
                language=case.language,
            ),
        )
        latency_ms = (time.perf_counter() - started) * 1000
        llm_meta = _llm_metadata(container)
        structured = response.structured_result
        schema_valid = False
        if structured is not None:
            ARTIFACT_MODELS[RESULT_ARTIFACT[case.workflow]].model_validate(structured)
            schema_valid = True
        return EvalRecord(
            provider=provider,
            model=llm_meta.get("model"),
            workflow=case.workflow.value,
            case_id=case.case_id,
            success=response.status == "ok",
            latency_ms=round(latency_ms, 1),
            schema_valid=schema_valid,
            status=response.status,
            result=structured,
        )
    except Exception as exc:  # recorded, never raised: one failing provider must not stop the run
        return EvalRecord(
            provider=provider,
            model=None,
            workflow=case.workflow.value,
            case_id=case.case_id,
            success=False,
            latency_ms=round((time.perf_counter() - started) * 1000, 1),
            schema_valid=False,
            error=f"{type(exc).__name__}: {exc}",
        )
    finally:
        await container.aclose()


def _llm_metadata(container: Any) -> dict[str, Any]:
    for event in reversed(container.trace.events):
        if event.stage == "generate" and event.status == "completed":
            return dict(event.metadata)
    return {}


async def compare(providers: list[str], cases: list[EvalCase], base: AppSettings | None = None) -> list[EvalRecord]:
    records: list[EvalRecord] = []
    for provider in providers:
        try:
            settings = settings_for(provider, base)
        except ValueError as exc:
            errors = getattr(exc, "errors", None)
            reason = errors()[0]["msg"] if callable(errors) else str(exc)
            records.extend(
                EvalRecord(provider, None, c.workflow.value, c.case_id, False, 0.0, False, error=f"not configured: {reason}")
                for c in cases
            )
            continue
        for case in cases:
            records.append(await run_case(provider, case, settings))
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--providers", default="fake", help=f"comma-separated subset of {','.join(PROVIDERS)}")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_DIR, help="JSON file or directory of JSON files")
    parser.add_argument("--workflow", choices=[w.value for w in WorkflowName], help="only run this workflow")
    parser.add_argument("--output", type=Path, help="write JSON report here (default: stdout)")
    args = parser.parse_args(argv)

    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    unknown = sorted(set(providers) - set(PROVIDERS))
    if unknown:
        parser.error(f"unknown providers: {', '.join(unknown)}")
    cases = load_cases(args.cases)
    if args.workflow:
        cases = [c for c in cases if c.workflow.value == args.workflow]

    records = asyncio.run(compare(providers, cases))
    report = json.dumps([asdict(r) for r in records], ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n", encoding="utf-8")
    else:
        print(report)
    for r in records:
        print(
            f"{r.provider:9} {r.workflow:9} {r.case_id:24} ok={r.success!s:5} "
            f"schema={r.schema_valid!s:5} {r.latency_ms:8.1f} ms {r.error or ''}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
