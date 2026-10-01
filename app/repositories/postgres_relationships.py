from __future__ import annotations

from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.artifacts import RelationshipRule
from app.persistence.postgres import RelationshipModel, RelationshipRuleModel
from app.repositories.relationships import (
    RelationshipCreate,
    RelationshipRecord,
    RelationshipRepository,
    RelationshipUpdate,
)


class PostgresRelationshipRepository(RelationshipRepository):
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self.sessions = sessions

    @staticmethod
    def _to_record(model: RelationshipModel) -> RelationshipRecord:
        return RelationshipRecord(
            relationship_id=model.relationship_id,
            user_id=model.user_id,
            relation_type=model.relation_type,
            aliases=list(model.aliases or []),
            rules=[
                RelationshipRule(
                    id=rule.id,
                    type=rule.type,
                    value=rule.value,
                    priority=rule.priority,
                    created_at=rule.created_at,
                )
                for rule in model.rules
            ],
            communication_style=dict(model.communication_style or {}),
            ruleset_version=model.ruleset_version,
        )

    @staticmethod
    def _query(user_id: str, relationship_id: str):
        return (
            select(RelationshipModel)
            .options(selectinload(RelationshipModel.rules))
            .where(
                RelationshipModel.relationship_id == relationship_id,
                RelationshipModel.user_id == user_id,
            )
        )

    async def get(self, user_id: str, relationship_id: str | None) -> RelationshipRecord | None:
        if relationship_id is None:
            return None
        async with self.sessions() as session:
            model = (await session.execute(self._query(user_id, relationship_id))).scalar_one_or_none()
            return self._to_record(model) if model else None

    async def list_for_user(self, user_id: str) -> list[RelationshipRecord]:
        async with self.sessions() as session:
            statement = (
                select(RelationshipModel)
                .options(selectinload(RelationshipModel.rules))
                .where(RelationshipModel.user_id == user_id)
                .order_by(RelationshipModel.created_at.asc())
            )
            models = (await session.execute(statement)).scalars().all()
            return [self._to_record(model) for model in models]

    async def create(self, user_id: str, value: RelationshipCreate) -> RelationshipRecord:
        async with self.sessions() as session:
            model = RelationshipModel(
                relationship_id=f"rel_{uuid4().hex}",
                user_id=user_id,
                relation_type=value.relation_type,
                aliases=list(value.aliases),
                communication_style=dict(value.communication_style),
                ruleset_version=1,
            )
            session.add(model)
            await session.commit()
            model = (await session.execute(self._query(user_id, model.relationship_id))).scalar_one()
            return self._to_record(model)

    async def update(self, user_id: str, relationship_id: str, value: RelationshipUpdate) -> RelationshipRecord:
        async with self.sessions() as session:
            model = (await session.execute(self._query(user_id, relationship_id))).scalar_one_or_none()
            if model is None:
                raise KeyError(f"Unknown relationship {relationship_id}")
            if value.relation_type is not None:
                model.relation_type = value.relation_type
            if value.aliases is not None:
                model.aliases = list(value.aliases)
            if value.communication_style is not None:
                model.communication_style = dict(value.communication_style)
            model.ruleset_version += 1
            await session.commit()
            model = (await session.execute(self._query(user_id, relationship_id))).scalar_one()
            return self._to_record(model)

    async def delete(self, user_id: str, relationship_id: str) -> bool:
        async with self.sessions() as session:
            result = await session.execute(
                delete(RelationshipModel).where(
                    RelationshipModel.relationship_id == relationship_id,
                    RelationshipModel.user_id == user_id,
                )
            )
            await session.commit()
            return bool(result.rowcount)

    async def add_rule(self, user_id: str, relationship_id: str, rule: RelationshipRule) -> RelationshipRule:
        async with self.sessions() as session:
            relationship = (
                await session.execute(
                    select(RelationshipModel).where(
                        RelationshipModel.relationship_id == relationship_id,
                        RelationshipModel.user_id == user_id,
                    )
                )
            ).scalar_one_or_none()
            if relationship is None:
                raise KeyError(f"Unknown relationship {relationship_id}")
            model = RelationshipRuleModel(
                relationship_id=relationship_id,
                type=rule.type,
                value=rule.value,
                priority=rule.priority,
            )
            session.add(model)
            relationship.ruleset_version += 1
            await session.commit()
            await session.refresh(model)
            return RelationshipRule(
                id=model.id,
                type=model.type,
                value=model.value,
                priority=model.priority,
                created_at=model.created_at,
            )

    async def update_rule(
        self,
        user_id: str,
        relationship_id: str,
        rule_id: int,
        rule: RelationshipRule,
    ) -> RelationshipRule:
        async with self.sessions() as session:
            relationship = (
                await session.execute(
                    select(RelationshipModel).where(
                        RelationshipModel.relationship_id == relationship_id,
                        RelationshipModel.user_id == user_id,
                    )
                )
            ).scalar_one_or_none()
            if relationship is None:
                raise KeyError(f"Unknown relationship {relationship_id}")
            model = (
                await session.execute(
                    select(RelationshipRuleModel).where(
                        RelationshipRuleModel.id == rule_id,
                        RelationshipRuleModel.relationship_id == relationship_id,
                    )
                )
            ).scalar_one_or_none()
            if model is None:
                raise KeyError(f"Unknown relationship rule {rule_id}")
            model.type = rule.type
            model.value = rule.value
            model.priority = rule.priority
            relationship.ruleset_version += 1
            await session.commit()
            await session.refresh(model)
            return RelationshipRule(
                id=model.id,
                type=model.type,
                value=model.value,
                priority=model.priority,
                created_at=model.created_at,
            )

    async def delete_rule(self, user_id: str, relationship_id: str, rule_id: int) -> bool:
        async with self.sessions() as session:
            relationship = (
                await session.execute(
                    select(RelationshipModel).where(
                        RelationshipModel.relationship_id == relationship_id,
                        RelationshipModel.user_id == user_id,
                    )
                )
            ).scalar_one_or_none()
            if relationship is None:
                return False
            result = await session.execute(
                delete(RelationshipRuleModel).where(
                    RelationshipRuleModel.id == rule_id,
                    RelationshipRuleModel.relationship_id == relationship_id,
                )
            )
            if result.rowcount:
                relationship.ruleset_version += 1
            await session.commit()
            return bool(result.rowcount)
