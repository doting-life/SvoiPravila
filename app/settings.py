from __future__ import annotations

from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "production"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    llm_provider: Literal["fake", "openai"] = "fake"
    openai_api_key: SecretStr | None = None
    openai_model: str | None = None
    openai_timeout_seconds: float = 30.0
    openai_max_retries: int = 2

    relationship_backend: Literal["memory", "postgres"] = "memory"
    database_url: str | None = None

    checkpoint_backend: Literal["memory", "redis"] = "memory"
    redis_url: str | None = None
    redis_checkpoint_ttl_seconds: int = 1200

    telegram_enabled: bool = False
    telegram_bot_token: SecretStr | None = None
    telegram_webhook_secret: SecretStr | None = None
    telegram_webhook_url: str | None = None
    telegram_default_workflow: Literal["soften", "decode", "help-say"] = "soften"
    telegram_init_data_max_age_seconds: int = 3600

    @model_validator(mode="after")
    def validate_production_dependencies(self) -> "AppSettings":
        if self.llm_provider == "openai":
            if self.openai_api_key is None:
                raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
            if not self.openai_model:
                raise ValueError("OPENAI_MODEL is required when LLM_PROVIDER=openai")
        if self.relationship_backend == "postgres" and not self.database_url:
            raise ValueError("DATABASE_URL is required when RELATIONSHIP_BACKEND=postgres")
        if self.checkpoint_backend == "redis" and not self.redis_url:
            raise ValueError("REDIS_URL is required when CHECKPOINT_BACKEND=redis")
        if self.telegram_enabled and self.telegram_bot_token is None:
            raise ValueError("TELEGRAM_BOT_TOKEN is required when TELEGRAM_ENABLED=true")
        if self.app_env == "production" and self.telegram_enabled and self.telegram_webhook_secret is None:
            raise ValueError("TELEGRAM_WEBHOOK_SECRET is required for Telegram in production")
        return self
