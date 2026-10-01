# Relationship Rules Skill

## Purpose

Relationship rules — явные настройки пользователя для конкретного адресата. Считай их более приоритетными, чем общие stylistic defaults, но ниже safety/policy constraints.

## Interpretation order

1. Safety constraints.
2. Explicit current user instruction.
3. Relationship rules.
4. Relationship communication style.
5. Workflow defaults.

## Conflicts

Если два relationship rules конфликтуют:
- выбирай более конкретное правило;
- если specificity равна, используй более новое правило;
- если конфликт всё ещё неоднозначен, не выдумывай новое правило: придерживайся более нейтральной формулировки.

## Prohibited behavior

- Не превращай preference в новый факт.
- Не приписывай адресату психологические свойства из relationship settings.
- Не цитируй внутренние rules в финальном сообщении, если пользователь этого не просил.
