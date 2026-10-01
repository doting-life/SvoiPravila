from app.artifacts import MessageRequest
from app.config import StageManifest
from app.stages.base import BaseStage, StageContext
from app.workflows.state import WorkflowState


class ReceiveStage(BaseStage):
    async def execute(self, state: WorkflowState, manifest: StageManifest, context: StageContext) -> MessageRequest:
        return MessageRequest(
            request_id=state.request_id,
            user_id=context.api_request.user_id,
            workflow=context.workflow_name,
            text=context.api_request.text,
            relationship_id=context.api_request.relationship_id,
            language=context.api_request.language,
        )
