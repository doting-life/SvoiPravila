from app.artifacts import GenerationPlan, RelationshipContext, SafetyDecision, WorkflowName
from app.config import StageManifest
from app.stages.base import BaseStage, StageContext
from app.workflows.state import WorkflowState


class PlanningStage(BaseStage):
    async def execute(self, state: WorkflowState, manifest: StageManifest, context: StageContext) -> GenerationPlan:
        safety = state.artifacts["safety_decision"]
        relationship = state.artifacts["relationship_context"]
        assert isinstance(safety, SafetyDecision)
        assert isinstance(relationship, RelationshipContext)

        skill_name = str(manifest.config["skill"])
        skill_version = str(manifest.config.get("skill_version", "1.0"))
        output_artifact = str(manifest.config["output_artifact"])

        constraints = list(safety.instructions)
        constraints.extend(rule.value for rule in sorted(relationship.rules, key=lambda rule: rule.priority, reverse=True))

        tone = None
        if relationship.communication_style:
            tone = str(relationship.communication_style.get("tone") or relationship.communication_style.get("firmness") or "") or None

        objective = context.workflow_manifest.description
        return GenerationPlan(
            request_id=state.request_id,
            workflow=WorkflowName(context.workflow_manifest.name),
            skill_name=skill_name,
            skill_version=skill_version,
            objective=objective,
            tone=tone,
            constraints=constraints,
            output_schema=output_artifact,
            provider_preferences={},
        )
