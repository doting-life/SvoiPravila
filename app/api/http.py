from __future__ import annotations

from fastapi import APIRouter, Request

from app.artifacts import AssistRequest, DeliveryResponse, WorkflowName


router = APIRouter()


async def _execute(request: Request, workflow: WorkflowName, body: AssistRequest) -> DeliveryResponse:
    container = request.app.state.container
    return await container.engine.execute(workflow, body)


@router.post("/v1/assist/soften", response_model=DeliveryResponse)
async def soften(request: Request, body: AssistRequest) -> DeliveryResponse:
    return await _execute(request, WorkflowName.SOFTEN, body)


@router.post("/v1/assist/decode", response_model=DeliveryResponse)
async def decode(request: Request, body: AssistRequest) -> DeliveryResponse:
    return await _execute(request, WorkflowName.DECODE, body)


@router.post("/v1/assist/help-say", response_model=DeliveryResponse)
async def help_say(request: Request, body: AssistRequest) -> DeliveryResponse:
    return await _execute(request, WorkflowName.HELP_SAY, body)
