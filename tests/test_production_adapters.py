from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.artifacts import SoftenResult, WorkflowName
from app.checkpoints import CheckpointSnapshot, RedisCheckpointStore
from app.integrations.telegram import parse_inline_query, parse_message_command
from app.persistence import RelationshipModel, RelationshipRuleModel
from app.repositories import PostgresRelationshipRepository
from app.settings import AppSettings
from app.tools.llm.base import StructuredGenerationRequest
from app.tools.llm.openai_provider import OpenAIStructuredLLMProvider


class FakeRedis:
    def __init__(self) -> None:
        self.items: dict[str, str] = {}

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.items[key] = value

    async def get(self, key: str):
        return self.items.get(key)

    async def delete(self, key: str) -> None:
        self.items.pop(key, None)


@pytest.mark.asyncio
async def test_redis_checkpoint_adapter_roundtrip() -> None:
    redis = FakeRedis()
    store = RedisCheckpointStore(redis, ttl_seconds=60)
    request_id = uuid4()
    snapshot = CheckpointSnapshot(
        request_id=request_id,
        workflow="soften",
        stage="generate",
        status="in_progress",
        state={"hello": "world"},
    )
    await store.save(snapshot)
    loaded = await store.load(request_id)
    assert loaded is not None
    assert loaded.request_id == request_id
    assert loaded.state == {"hello": "world"}
    await store.delete(request_id)
    assert await store.load(request_id) is None


class FakeScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeSession:
    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, statement):
        return FakeScalarResult(self.value)


class FakeSessionFactory:
    def __init__(self, value):
        self.value = value

    def __call__(self):
        return FakeSession(self.value)


@pytest.mark.asyncio
async def test_postgres_repository_maps_database_model_to_domain_record() -> None:
    relationship = RelationshipModel(
        relationship_id="partner-42",
        user_id="tg-100",
        relation_type="partner",
        aliases=["Аня"],
        communication_style={"firmness": "direct"},
        ruleset_version=3,
    )
    relationship.rules = [
        RelationshipRuleModel(
            type="avoid",
            value="не использовать 'ты всегда'",
            priority=100,
            created_at=datetime.now(timezone.utc),
        )
    ]
    repo = PostgresRelationshipRepository(FakeSessionFactory(relationship))  # type: ignore[arg-type]
    record = await repo.get("tg-100", "partner-42")
    assert record is not None
    assert record.ruleset_version == 3
    assert record.aliases == ["Аня"]
    assert record.rules[0].priority == 100


def test_telegram_workflow_parsing() -> None:
    assert parse_inline_query("decode: что он имел в виду?").workflow is WorkflowName.DECODE
    assert parse_inline_query("смягчить: Ты опять опоздал").text == "Ты опять опоздал"
    assert parse_message_command("/say Мне это не подходит").workflow is WorkflowName.HELP_SAY
    assert parse_inline_query("обычный текст").workflow is WorkflowName.SOFTEN


def test_settings_require_credentials_for_selected_production_adapters() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        AppSettings(llm_provider="openai", openai_model="some-model")
    with pytest.raises(ValueError, match="DATABASE_URL"):
        AppSettings(relationship_backend="postgres")
    with pytest.raises(ValueError, match="REDIS_URL"):
        AppSettings(checkpoint_backend="redis")
    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
        AppSettings(telegram_enabled=True)


@pytest.mark.asyncio
async def test_openai_provider_uses_parsed_pydantic_output() -> None:
    request_id = uuid4()
    parsed = SoftenResult(
        request_id=request_id,
        original_intent="Ты опять опоздал",
        rewritten_message="Мне неприятно, что ты снова опоздал.",
        tone_applied="calm_direct",
    )

    class FakeResponses:
        async def parse(self, **kwargs):
            assert kwargs["model"] == "test-model"
            assert kwargs["text_format"] is SoftenResult
            return SimpleNamespace(
                output_parsed=parsed,
                usage=SimpleNamespace(input_tokens=12, output_tokens=8),
            )

    fake_client = SimpleNamespace(responses=FakeResponses())
    provider = OpenAIStructuredLLMProvider(
        api_key="test-key", model="test-model", client=fake_client
    )
    response = await provider.generate(
        StructuredGenerationRequest(
            system_instructions="Return structured data.",
            user_payload={"message_request": {"request_id": str(request_id), "text": "Ты опять опоздал"}},
            output_model=SoftenResult,
            metadata={},
        )
    )

    assert response.provider == "openai"
    assert response.model == "test-model"
    assert response.input_tokens == 12
    assert response.payload["rewritten_message"].startswith("Мне неприятно")

