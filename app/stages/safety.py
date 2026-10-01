from app.artifacts import MessageRequest, SafetyDecision, WorkflowName
from app.config import StageManifest
from app.stages.base import BaseStage, StageContext
from app.workflows.state import WorkflowState


class SafetyStage(BaseStage):
    """Deterministic MVP safety envelope.

    Production should replace/extend this with a dedicated safety classifier.
    The stage already owns the policy boundary so doing that will not affect the
    workflow engine or generation skills.
    """

    async def execute(self, state: WorkflowState, manifest: StageManifest, context: StageContext) -> SafetyDecision:
        request = state.artifacts["message_request"]
        assert isinstance(request, MessageRequest)

        instructions: list[str] = []
        categories: list[str] = []

        if request.workflow is WorkflowName.DECODE:
            instructions.extend([
                "Do not present hidden motives as facts.",
                "Do not diagnose the message author.",
                "Separate observation from inference and express uncertainty.",
            ])
            categories.append("interpretation_uncertainty")

        return SafetyDecision(
            request_id=state.request_id,
            status="allow_with_constraints" if instructions else "allow",
            categories=categories,
            instructions=instructions,
            user_message=None,
        )
