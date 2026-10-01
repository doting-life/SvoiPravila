from pathlib import Path

from app.artifacts import ARTIFACT_MODELS, WorkflowName
from app.config import CONFIG_DIR, load_workflow_manifest
from app.skills import SkillLoader


def test_workflow_dependencies_are_ordered_and_artifacts_known() -> None:
    for workflow in WorkflowName:
        manifest = load_workflow_manifest(workflow.value)
        produced: set[str] = set()
        assert manifest.stages[0].name == manifest.entrypoint
        for stage in manifest.stages:
            assert set(stage.requires).issubset(produced), (
                workflow.value,
                stage.name,
                stage.requires,
                produced,
            )
            assert stage.produces in ARTIFACT_MODELS
            produced.add(stage.produces)
        assert "delivery_response" in produced


def test_all_skill_sources_exist_and_bundles_load() -> None:
    loader = SkillLoader()
    for workflow in WorkflowName:
        bundle = loader.load_bundle(workflow.value)
        assert bundle[-1].name == workflow.value
        assert "safety-core" in [skill.name for skill in bundle]
        for skill in bundle:
            assert skill.body.strip()


def test_yaml_architecture_catalog_is_present() -> None:
    assert (CONFIG_DIR / "runtime" / "runtime.yaml").exists()
    assert len(list((CONFIG_DIR / "artifacts").glob("*.yaml"))) >= 8
    assert len(list((CONFIG_DIR / "workflows").glob("*.yaml"))) == 3
