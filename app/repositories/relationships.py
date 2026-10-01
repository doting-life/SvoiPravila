from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.artifacts import RelationshipRule


@dataclass(slots=True)
class RelationshipRecord:
    relationship_id: str
    user_id: str
    relation_type: str | None = None
    aliases: list[str] = field(default_factory=list)
    rules: list[RelationshipRule] = field(default_factory=list)
    communication_style: dict[str, Any] = field(default_factory=dict)
    ruleset_version: int = 1


@dataclass(slots=True)
class RelationshipCreate:
    relation_type: str | None = None
    aliases: list[str] = field(default_factory=list)
    communication_style: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RelationshipUpdate:
    relation_type: str | None = None
    aliases: list[str] | None = None
    communication_style: dict[str, Any] | None = None


class RelationshipRepository(ABC):
    @abstractmethod
    async def get(self, user_id: str, relationship_id: str | None) -> RelationshipRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def list_for_user(self, user_id: str) -> list[RelationshipRecord]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, user_id: str, value: RelationshipCreate) -> RelationshipRecord:
        raise NotImplementedError

    @abstractmethod
    async def update(self, user_id: str, relationship_id: str, value: RelationshipUpdate) -> RelationshipRecord:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, user_id: str, relationship_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def add_rule(self, user_id: str, relationship_id: str, rule: RelationshipRule) -> RelationshipRule:
        raise NotImplementedError

    @abstractmethod
    async def update_rule(
        self,
        user_id: str,
        relationship_id: str,
        rule_id: int,
        rule: RelationshipRule,
    ) -> RelationshipRule:
        raise NotImplementedError

    @abstractmethod
    async def delete_rule(self, user_id: str, relationship_id: str, rule_id: int) -> bool:
        raise NotImplementedError


class InMemoryRelationshipRepository(RelationshipRepository):
    def __init__(self) -> None:
        self._records: dict[tuple[str, str], RelationshipRecord] = {}
        self._next_rule_id = 1

    def upsert(self, record: RelationshipRecord) -> None:
        clone = deepcopy(record)
        for rule in clone.rules:
            if rule.id is None:
                rule.id = self._next_rule_id
                self._next_rule_id += 1
        self._records[(record.user_id, record.relationship_id)] = clone

    async def get(self, user_id: str, relationship_id: str | None) -> RelationshipRecord | None:
        if relationship_id is None:
            return None
        record = self._records.get((user_id, relationship_id))
        return deepcopy(record) if record else None

    async def list_for_user(self, user_id: str) -> list[RelationshipRecord]:
        values = [deepcopy(record) for (owner, _), record in self._records.items() if owner == user_id]
        return sorted(values, key=lambda item: item.relationship_id)

    async def create(self, user_id: str, value: RelationshipCreate) -> RelationshipRecord:
        relationship_id = f"rel_{uuid4().hex}"
        record = RelationshipRecord(
            relationship_id=relationship_id,
            user_id=user_id,
            relation_type=value.relation_type,
            aliases=list(value.aliases),
            communication_style=dict(value.communication_style),
            ruleset_version=1,
        )
        self.upsert(record)
        return deepcopy(self._records[(user_id, relationship_id)])

    async def update(self, user_id: str, relationship_id: str, value: RelationshipUpdate) -> RelationshipRecord:
        key = (user_id, relationship_id)
        record = self._records.get(key)
        if record is None:
            raise KeyError(f"Unknown relationship {relationship_id}")
        if value.relation_type is not None:
            record.relation_type = value.relation_type
        if value.aliases is not None:
            record.aliases = list(value.aliases)
        if value.communication_style is not None:
            record.communication_style = dict(value.communication_style)
        record.ruleset_version += 1
        return deepcopy(record)

    async def delete(self, user_id: str, relationship_id: str) -> bool:
        return self._records.pop((user_id, relationship_id), None) is not None

    async def add_rule(self, user_id: str, relationship_id: str, rule: RelationshipRule) -> RelationshipRule:
        record = self._records.get((user_id, relationship_id))
        if record is None:
            raise KeyError(f"Unknown relationship {relationship_id}")
        stored = deepcopy(rule)
        stored.id = self._next_rule_id
        self._next_rule_id += 1
        stored.created_at = stored.created_at or datetime.now(timezone.utc)
        record.rules.append(stored)
        record.rules.sort(key=lambda item: item.priority, reverse=True)
        record.ruleset_version += 1
        return deepcopy(stored)

    async def update_rule(
        self,
        user_id: str,
        relationship_id: str,
        rule_id: int,
        rule: RelationshipRule,
    ) -> RelationshipRule:
        record = self._records.get((user_id, relationship_id))
        if record is None:
            raise KeyError(f"Unknown relationship {relationship_id}")
        for index, existing in enumerate(record.rules):
            if existing.id == rule_id:
                updated = deepcopy(rule)
                updated.id = rule_id
                updated.created_at = existing.created_at
                record.rules[index] = updated
                record.rules.sort(key=lambda item: item.priority, reverse=True)
                record.ruleset_version += 1
                return deepcopy(updated)
        raise KeyError(f"Unknown relationship rule {rule_id}")

    async def delete_rule(self, user_id: str, relationship_id: str, rule_id: int) -> bool:
        record = self._records.get((user_id, relationship_id))
        if record is None:
            return False
        before = len(record.rules)
        record.rules = [rule for rule in record.rules if rule.id != rule_id]
        deleted = len(record.rules) != before
        if deleted:
            record.ruleset_version += 1
        return deleted

    @classmethod
    def demo(cls) -> "InMemoryRelationshipRepository":
        repo = cls()
        repo.upsert(
            RelationshipRecord(
                relationship_id="partner-1",
                user_id="u-1",
                relation_type="partner",
                aliases=["партнёр"],
                rules=[
                    RelationshipRule(
                        type="avoid",
                        value="не использовать категоричные 'ты всегда' и 'ты никогда'",
                        priority=100,
                        created_at=datetime.now(timezone.utc),
                    ),
                    RelationshipRule(
                        type="tone",
                        value="говорить прямо и естественно, без терапевтических штампов",
                        priority=90,
                        created_at=datetime.now(timezone.utc),
                    ),
                ],
                communication_style={"firmness": "direct", "verbosity": "short"},
                ruleset_version=1,
            )
        )
        return repo
