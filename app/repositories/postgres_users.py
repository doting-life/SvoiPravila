from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.integrations.telegram import TelegramWebAppUser
from app.persistence.postgres import UserModel
from app.repositories.users import UserRecord, UserRepository


class PostgresUserRepository(UserRepository):
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self.sessions = sessions

    @staticmethod
    def _to_record(model: UserModel) -> UserRecord:
        return UserRecord(
            user_id=model.user_id,
            telegram_user_id=model.telegram_user_id,
            first_name=model.first_name,
            last_name=model.last_name,
            username=model.username,
            language_code=model.language_code,
            default_relationship_id=model.default_relationship_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get(self, user_id: str) -> UserRecord | None:
        async with self.sessions() as session:
            model = (
                await session.execute(select(UserModel).where(UserModel.user_id == user_id))
            ).scalar_one_or_none()
            return self._to_record(model) if model else None

    async def get_by_telegram_id(self, telegram_user_id: int) -> UserRecord | None:
        async with self.sessions() as session:
            model = (
                await session.execute(
                    select(UserModel).where(UserModel.telegram_user_id == telegram_user_id)
                )
            ).scalar_one_or_none()
            return self._to_record(model) if model else None

    async def get_or_create_from_telegram(self, telegram_user: TelegramWebAppUser) -> UserRecord:
        async with self.sessions() as session:
            model = (
                await session.execute(
                    select(UserModel).where(UserModel.telegram_user_id == telegram_user.id)
                )
            ).scalar_one_or_none()
            now = datetime.now(timezone.utc)
            if model is None:
                model = UserModel(
                    user_id=f"usr_{uuid4().hex}",
                    telegram_user_id=telegram_user.id,
                    first_name=telegram_user.first_name,
                    last_name=telegram_user.last_name,
                    username=telegram_user.username,
                    language_code=telegram_user.language_code,
                )
                session.add(model)
            else:
                model.first_name = telegram_user.first_name
                model.last_name = telegram_user.last_name
                model.username = telegram_user.username
                model.language_code = telegram_user.language_code
                model.updated_at = now
            await session.commit()
            await session.refresh(model)
            return self._to_record(model)

    async def set_default_relationship(self, user_id: str, relationship_id: str | None) -> UserRecord:
        async with self.sessions() as session:
            model = (
                await session.execute(select(UserModel).where(UserModel.user_id == user_id))
            ).scalar_one_or_none()
            if model is None:
                raise KeyError(f"Unknown user {user_id}")
            model.default_relationship_id = relationship_id
            model.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(model)
            return self._to_record(model)
