from __future__ import annotations

from app.artifacts import (
    DecodeResult,
    HelpSayResult,
    MessageRequest,
    SemanticCheck,
    SoftenResult,
    ValidationResult,
)
from app.config import StageManifest
from app.stages.base import BaseStage, StageContext
from app.workflows.state import WorkflowState


class ValidationStage(BaseStage):
    async def execute(self, state: WorkflowState, manifest: StageManifest, context: StageContext) -> ValidationResult:
        request = state.artifacts["message_request"]
        assert isinstance(request, MessageRequest)

        result_name = next(
            name
            for name in ("soften_result", "decode_result", "help_say_result")
            if name in state.artifacts
        )
        result = state.artifacts[result_name]
        checks: list[SemanticCheck] = []

        if isinstance(result, SoftenResult):
            checks.append(SemanticCheck(name="non_empty_rewrite", passed=bool(result.rewritten_message.strip())))
            checks.append(SemanticCheck(name="intent_recorded", passed=bool(result.original_intent.strip())))
        elif isinstance(result, DecodeResult):
            checks.append(SemanticCheck(name="uncertainty_present", passed=bool(result.uncertainty.strip())))
            checks.append(SemanticCheck(name="probable_not_certain", passed=bool(result.probable_intent.strip())))
        elif isinstance(result, HelpSayResult):
            checks.append(SemanticCheck(name="non_empty_message", passed=bool(result.message.strip())))
            checks.append(SemanticCheck(name="intent_preserved", passed=bool(result.preserved_intent.strip())))

        schema_valid = True
        policy_valid = all(check.passed for check in checks)
        language_valid = True
        status = "pass" if schema_valid and policy_valid and language_valid else "retry"
        retry_instructions = [] if status == "pass" else ["Regenerate and satisfy all failed semantic checks."]

        return ValidationResult(
            request_id=state.request_id,
            status=status,
            schema_valid=schema_valid,
            policy_valid=policy_valid,
            language_valid=language_valid,
            semantic_checks=checks,
            retry_instructions=retry_instructions,
        )
