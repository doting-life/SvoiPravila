from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.config import CONFIG_DIR, SKILLS_DIR


@dataclass(frozen=True)
class LoadedSkill:
    name: str
    version: str
    kind: str
    body: str
    manifest: dict[str, Any]


class SkillLoader:
    def __init__(self, config_dir: Path = CONFIG_DIR, skills_dir: Path = SKILLS_DIR) -> None:
        self.config_dir = config_dir
        self.skills_dir = skills_dir

    @lru_cache(maxsize=64)
    def load(self, name: str) -> LoadedSkill:
        manifest_path = self._find_manifest(name)
        with manifest_path.open("r", encoding="utf-8") as handle:
            manifest = yaml.safe_load(handle) or {}
        source = manifest.get("source")
        if not source:
            raise ValueError(f"Skill manifest {manifest_path} has no source")
        source_path = self.skills_dir.parent / source
        body = source_path.read_text(encoding="utf-8")
        return LoadedSkill(
            name=manifest["name"],
            version=str(manifest["version"]),
            kind=manifest.get("type", "unknown"),
            body=body,
            manifest=manifest,
        )

    def load_bundle(self, workflow_skill_name: str) -> list[LoadedSkill]:
        workflow_skill = self.load(workflow_skill_name)
        core_names = workflow_skill.manifest.get("requires_core_skills", [])
        core_skills = [self.load(name) for name in core_names]
        core_skills.sort(key=lambda skill: int(skill.manifest.get("priority", 0)), reverse=True)
        return [*core_skills, workflow_skill]

    def _find_manifest(self, name: str) -> Path:
        candidates = list((self.config_dir / "skills").glob("**/*.yaml"))
        for path in candidates:
            with path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
            if data.get("name") == name:
                return path
        raise FileNotFoundError(f"Skill manifest not found for skill {name!r}")
