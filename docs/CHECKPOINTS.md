# Checkpoints

## Purpose

Checkpoint хранит краткоживущий execution state текущего запроса.

## Storage

MVP: Redis.

Рекомендуемый ключ:

```text
request:{request_id}
```

## Fields

- `request_id`
- `workflow`
- `current_stage`
- `status`
- `attempt`
- `completed_stages[]`
- `artifact_refs`
- `skill_version`
- `provider`
- `model`
- `started_at`
- `updated_at`
- `expires_at`

## Statuses

- `pending`
- `in_progress`
- `completed`
- `failed_retryable`
- `failed_terminal`

## Retry

Retry повторяет только текущую неуспешную stage, если предыдущие artifacts остаются валидными.

## Idempotency

Inbound Telegram update ID + workflow + normalized command могут использоваться как idempotency key для защиты от повторной доставки webhook.
