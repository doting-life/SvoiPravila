from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redis.asyncio import Redis
else:
    Redis = Any  # type: ignore[misc,assignment]
from sqlalchemy.ext.asyncio import AsyncEngine

from app.checkpoints import CheckpointStore, InMemoryCheckpointStore, RedisCheckpointStore
from app.integrations.telegram import TelegramBotClient
from app.observability import RequestTraceSink
from app.persistence import build_async_engine, build_session_factory
from app.repositories import (
    InMemoryRelationshipRepository,
    InMemoryUserRepository,
    PostgresRelationshipRepository,
    PostgresUserRepository,
    RelationshipRepository,
    UserRecord,
    UserRepository,
)
from app.settings import AppSettings
from app.skills import SkillLoader
from app.stages import StageRegistry
from app.tools.llm import FakeStructuredLLMProvider, LLMGenerateTool, OpenAIStructuredLLMProvider
from app.tools.registry import ToolRegistry
from app.workflows.engine import WorkflowDependencies, WorkflowEngine


AsyncCloser = Callable[[], Awaitable[Any]]


@dataclass(slots=True)
class ApplicationContainer:
    engine: WorkflowEngine
    trace: RequestTraceSink
    checkpoints: CheckpointStore
    relationships: RelationshipRepository
    users: UserRepository
    telegram: TelegramBotClient | None = None
    redis: Redis | None = None
    database_engine: AsyncEngine | None = None
    _closers: list[AsyncCloser] = field(default_factory=list, repr=False)

    async def aclose(self) -> None:
        for closer in reversed(self._closers):
            await closer()


def build_container(settings: AppSettings | None = None) -> ApplicationContainer:
    settings = settings or AppSettings()
    closers: list[AsyncCloser] = []

    tools = ToolRegistry()
    if settings.llm_provider == "openai":
        provider = OpenAIStructuredLLMProvider(
            api_key=settings.openai_api_key.get_secret_value(),  # type: ignore[union-attr]
            model=settings.openai_model or "",
            timeout_seconds=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
        )
        closers.append(provider.aclose)
    else:
        provider = FakeStructuredLLMProvider()
    tools.register(LLMGenerateTool(provider))

    redis: Redis | None = None
    if settings.checkpoint_backend == "redis":
        try:
            from redis.asyncio import Redis as RedisClient
        except ModuleNotFoundError as exc:
            raise RuntimeError("redis package is required when CHECKPOINT_BACKEND=redis") from exc
        redis = RedisClient.from_url(settings.redis_url or "", decode_responses=True)
        checkpoints: CheckpointStore = RedisCheckpointStore(
            redis,
            ttl_seconds=settings.redis_checkpoint_ttl_seconds,
        )
        closers.append(redis.aclose)
    else:
        checkpoints = InMemoryCheckpointStore()

    database_engine: AsyncEngine | None = None
    if settings.relationship_backend == "postgres":
        database_engine = build_async_engine(settings.database_url or "")
        sessions = build_session_factory(database_engine)
        relationships: RelationshipRepository = PostgresRelationshipRepository(sessions)
        users: UserRepository = PostgresUserRepository(sessions)
        closers.append(database_engine.dispose)
    else:
        relationships = InMemoryRelationshipRepository.demo()
        memory_users = InMemoryUserRepository()
        memory_users.upsert(
            UserRecord(
                user_id="u-1",
                telegram_user_id=100001,
                first_name="Demo",
                language_code="ru",
                default_relationship_id="partner-1",
            )
        )
        users = memory_users

    telegram: TelegramBotClient | None = None
    if settings.telegram_enabled:
        telegram = TelegramBotClient(settings.telegram_bot_token.get_secret_value())  # type: ignore[union-attr]
        closers.append(telegram.aclose)

    trace = RequestTraceSink()
    engine = WorkflowEngine(
        WorkflowDependencies(
            skills=SkillLoader(),
            tools=tools,
            relationships=relationships,
            users=users,
            checkpoints=checkpoints,
            trace=trace,
            stages=StageRegistry(),
        )
    )
    return ApplicationContainer(
        engine=engine,
        trace=trace,
        checkpoints=checkpoints,
        relationships=relationships,
        users=users,
        telegram=telegram,
        redis=redis,
        database_engine=database_engine,
        _closers=closers,
    )
