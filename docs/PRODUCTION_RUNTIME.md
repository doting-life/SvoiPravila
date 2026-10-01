# Production Runtime — v0.2

## Dependency selection

The workflow core has no direct dependency on OpenAI, PostgreSQL, Redis, or
Telegram. `AppSettings` selects concrete adapters at application startup.

```text
WorkflowEngine
  |-- StructuredLLMProvider -> fake | OpenAI
  |-- RelationshipRepository -> memory | PostgreSQL
  |-- CheckpointStore -> memory | Redis
  `-- ingress -> HTTP | Telegram webhook
```

## OpenAI

`OpenAIStructuredLLMProvider` uses the Responses API structured-output parser
with a Pydantic artifact model. The provider returns already parsed data to
`LLMGenerateTool`; the tool performs a second domain-model validation before the
artifact enters workflow state.

Required environment variables when selected:

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=...
```

The model name is intentionally not hard-coded because model availability and
selection are deployment decisions.

## PostgreSQL

The production relationship repository stores only durable user configuration:
relationship identity, aliases, communication style, rules, priorities, and
ruleset version. Raw workflow messages are not written to these tables.

For development schema bootstrap:

```bash
python scripts/init_db.py
```

Alembic migrations remain a later hardening step.

## Redis

Redis contains transient resumable workflow state. The checkpoint TTL defaults
to 1200 seconds and is controlled by `REDIS_CHECKPOINT_TTL_SECONDS`.

Redis can therefore contain the active request text temporarily. This is
intentional for resume semantics and is distinct from durable PostgreSQL
storage. Production Redis should use encryption-in-transit/access controls
appropriate to the deployment environment.

## Telegram

Telegram ingress is deliberately thin. The adapter parses a workflow command,
creates an `AssistRequest`, invokes the same `WorkflowEngine` used by HTTP, and
converts the `DeliveryResponse` back to Telegram.

Supported v0.2 prefixes:

- `soften:` / `смягчить:`
- `decode:` / `расшифровать:`
- `help-say:` / `скажи:`
- direct commands `/soften`, `/decode`, `/say`

The webhook endpoint acknowledges the update immediately and performs the LLM
work as a FastAPI background task before calling Telegram's Bot API.

Inline results use `cache_time=0` and `is_personal=true` because generated text
is user-specific.
