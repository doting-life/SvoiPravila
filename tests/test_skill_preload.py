from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import app.container as container_module
import app.skills.loader as loader_module
from app.artifacts import AssistRequest, WorkflowName
from app.config import CONFIG_DIR, SKILLS_DIR
from app.container import WORKFLOW_SKILLS, build_container
from app.settings import AppSettings
from app.skills import SkillLoader


def _settings() -> AppSettings:
    return AppSettings(_env_file=None)


class RecordingSkillLoader(SkillLoader):
    instances: list[RecordingSkillLoader] = []

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.bundles: list[str] = []
        RecordingSkillLoader.instances.append(self)

    def load_bundle(self, workflow_skill_name: str):
        self.bundles.append(workflow_skill_name)
        return super().load_bundle(workflow_skill_name)


@pytest.fixture
def recording_loader(monkeypatch):
    RecordingSkillLoader.instances = []
    monkeypatch.setattr(container_module, "SkillLoader", RecordingSkillLoader)
    return RecordingSkillLoader


def _copy_skills(tmp_path: Path) -> tuple[Path, Path]:
    config_dir = tmp_path / "config"
    skills_dir = tmp_path / "skills"
    shutil.copytree(CONFIG_DIR / "skills", config_dir / "skills")
    shutil.copytree(SKILLS_DIR, skills_dir)
    return config_dir, skills_dir


def _use_loader_at(monkeypatch, config_dir: Path, skills_dir: Path) -> None:
    monkeypatch.setattr(
        container_module, "SkillLoader", lambda: SkillLoader(config_dir=config_dir, skills_dir=skills_dir)
    )


def test_workflow_skills_are_the_current_workflows() -> None:
    assert set(WORKFLOW_SKILLS) == {w.value for w in WorkflowName}


@pytest.mark.asyncio
async def test_build_container_preloads_all_workflow_skills(recording_loader) -> None:
    container = build_container(_settings())
    try:
        assert len(recording_loader.instances) == 1
        assert recording_loader.instances[0].bundles == ["soften", "decode", "help-say"]
    finally:
        await container.aclose()


@pytest.mark.asyncio
async def test_generation_reuses_preloaded_loader_without_disk_reads(recording_loader, monkeypatch) -> None:
    container = build_container(_settings())
    loader = recording_loader.instances[0]

    def no_disk(*args, **kwargs):
        raise AssertionError("skill files were read after startup")

    # Only SkillLoader disk access: manifest lookup and Markdown source reads.
    monkeypatch.setattr(loader_module.SkillLoader, "_find_manifest", no_disk)
    monkeypatch.setattr(loader_module.Path, "read_text", no_disk)
    try:
        for workflow in WorkflowName:
            response = await container.engine.execute(
                workflow, AssistRequest(user_id="u-1", text="test message", relationship_id="partner-1")
            )
            assert response.status == "ok"
    finally:
        await container.aclose()

    assert len(recording_loader.instances) == 1
    assert loader.bundles[len(WORKFLOW_SKILLS) :] == [w.value for w in WorkflowName]


def _remove_decode_source(config_dir: Path, skills_dir: Path) -> None:
    (skills_dir / "workflows" / "decode.md").unlink()


def _remove_help_say_manifest(config_dir: Path, skills_dir: Path) -> None:
    (config_dir / "skills" / "workflows" / "help-say.yaml").unlink()


def _strip_soften_source(config_dir: Path, skills_dir: Path) -> None:
    (config_dir / "skills" / "workflows" / "soften.yaml").write_text("name: soften\nversion: 1\n", encoding="utf-8")


@pytest.mark.parametrize(
    ("break_skill", "skill"),
    [
        (_remove_decode_source, "decode"),
        (_remove_help_say_manifest, "help-say"),
        (_strip_soften_source, "soften"),
    ],
    ids=["missing-source", "missing-manifest", "manifest-without-source"],
)
def test_broken_workflow_skill_fails_container_construction(tmp_path, monkeypatch, break_skill, skill) -> None:
    config_dir, skills_dir = _copy_skills(tmp_path)
    break_skill(config_dir, skills_dir)
    _use_loader_at(monkeypatch, config_dir, skills_dir)

    with pytest.raises(RuntimeError, match=f"Failed to preload workflow skill .{skill}."):
        build_container(_settings())


def test_app_startup_fails_on_broken_skill(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    config_dir, skills_dir = _copy_skills(tmp_path)
    (skills_dir / "workflows" / "soften.md").unlink()
    _use_loader_at(monkeypatch, config_dir, skills_dir)
    monkeypatch.setattr("app.main.AppSettings", _settings)

    with pytest.raises(RuntimeError, match="Failed to preload workflow skill .soften."):
        with TestClient(app):
            pass
