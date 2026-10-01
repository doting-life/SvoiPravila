# Artifacts

Artifacts — единственный официальный способ передачи данных между stages.

## MessageRequest

Назначение: нормализованный пользовательский запрос.

Минимальные поля:
- `version`
- `request_id`
- `user_id`
- `workflow`
- `text`
- `relationship_id`
- `language`
- `created_at`

## SafetyDecision

Поля:
- `status`: `allow | allow_with_constraints | block`
- `categories[]`
- `instructions[]`
- `user_message` — только если запрос блокируется/ограничивается.

## RelationshipContext

Поля:
- `relationship_id`
- `relation_type`
- `aliases[]`
- `rules[]`
- `communication_style`
- `ruleset_version`

## GenerationPlan

Поля:
- `workflow`
- `skill_name`
- `skill_version`
- `objective`
- `tone`
- `constraints[]`
- `output_schema`
- `provider_preferences`

## SoftenResult

Поля:
- `original_intent`
- `rewritten_message`
- `tone_applied`
- `constraints_respected[]`

## DecodeResult

Поля:
- `literal_meaning`
- `probable_intent`
- `emotional_tone`
- `uncertainty`
- `alternative_interpretations[]`

## HelpSayResult

Поля:
- `message`
- `tone`
- `preserved_intent`
- `warnings[]`

## ValidationResult

Поля:
- `status`: `pass | retry | block`
- `schema_valid`
- `policy_valid`
- `language_valid`
- `semantic_checks[]`
- `retry_instructions[]`
