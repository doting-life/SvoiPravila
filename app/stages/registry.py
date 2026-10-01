from __future__ import annotations

from app.stages.base import BaseStage
from app.stages.context import ContextStage
from app.stages.delivery import DeliveryStage
from app.stages.generation import GenerationStage
from app.stages.planning import PlanningStage
from app.stages.receive import ReceiveStage
from app.stages.safety import SafetyStage
from app.stages.validation import ValidationStage


class StageRegistry:
    def __init__(self) -> None:
        instances: list[BaseStage] = [
            ReceiveStage(),
            SafetyStage(),
            ContextStage(),
            PlanningStage(),
            GenerationStage(),
            ValidationStage(),
            DeliveryStage(),
        ]
        self._by_class_name = {stage.__class__.__name__: stage for stage in instances}

    def resolve(self, handler: str) -> BaseStage:
        class_name = handler.rsplit(".", 1)[-1]
        try:
            return self._by_class_name[class_name]
        except KeyError as exc:
            raise KeyError(f"Unknown stage handler: {handler}") from exc
