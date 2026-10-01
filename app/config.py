from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
SKILLS_DIR = PROJECT_ROOT / "skills"


class RetryConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    max_attempts: int = 1
    retry_stage: str | None = None


class StageManifest(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    handler: str
    requires: list[str] = Field(default_factory=list)
    produces: str
    tools: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
    retry: RetryConfig | None = None


class WorkflowManifest(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    version: str
    description: str
    entrypoint: str
    stages: list[StageManifest]
    policies: dict[str, Any] = Field(default_factory=dict)


class RuntimeSettings(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: str
    workflow_engine: dict[str, Any]
    checkpoint: dict[str, Any]
    privacy: dict[str, Any]
    observability: dict[str, Any]
    llm: dict[str, Any]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


@lru_cache(maxsize=16)
def load_workflow_manifest(name: str) -> WorkflowManifest:
    path = CONFIG_DIR / "workflows" / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Workflow manifest not found: {path}")
    return WorkflowManifest.model_validate(load_yaml(path))


@lru_cache(maxsize=1)
def load_runtime_settings() -> RuntimeSettings:
    return RuntimeSettings.model_validate(load_yaml(CONFIG_DIR / "runtime" / "runtime.yaml"))
