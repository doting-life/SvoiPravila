from app.artifacts import MessageRequest, RelationshipContext
from app.config import StageManifest
from app.stages.base import BaseStage, StageContext
from app.workflows.state import WorkflowState


class ContextStage(BaseStage):
    async def execute(self, state: WorkflowState, manifest: StageManifest, context: StageContext) -> RelationshipContext:
        request = state.artifacts["message_request"]
        assert isinstance(request, MessageRequest)

        relationship_id = request.relationship_id
        if relationship_id is None:
            user = await context.users.get(request.user_id)
            if user is not None:
                relationship_id = user.default_relationship_id

        record = await context.relationships.get(request.user_id, relationship_id)
        if record is None:
            return RelationshipContext(
                request_id=state.request_id,
                relationship_id=relationship_id,
                relation_type=None,
                aliases=[],
                rules=[],
                communication_style={},
                ruleset_version=0,
            )
        return RelationshipContext(
            request_id=state.request_id,
            relationship_id=record.relationship_id,
            relation_type=record.relation_type,
            aliases=record.aliases,
            rules=record.rules,
            communication_style=record.communication_style,
            ruleset_version=record.ruleset_version,
        )
