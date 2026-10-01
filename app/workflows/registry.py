from __future__ import annotations

from app.artifacts import WorkflowName
from app.config import WorkflowManifest, load_workflow_manifest


class WorkflowRegistry:
    def get(self, workflow: WorkflowName | str) -> WorkflowManifest:
        name = workflow.value if isinstance(workflow, WorkflowName) else workflow
        return load_workflow_manifest(name)

    def list(self) -> list[str]:
        return [workflow.value for workflow in WorkflowName]
