v0.4

## Core already implemented

- Deterministic YAML-driven workflow engine.
- Strict stage dependency checks.
- Typed Pydantic artifacts.
- Markdown/YAML skill loading.
- Tool registry.
- Resume after failed stage and manifest-controlled retry.
- Technical tracing without raw prompt/message logging.
- FastAPI assist endpoints for `soften`, `decode`, and `help-say`.

## Production adapters from v0.2

- OpenAI Structured Outputs provider through the Responses API SDK parser.
- PostgreSQL async persistence.
- Redis checkpoint store with TTL.
- Telegram Bot webhook, webhook-secret verification, Inline Mode, and direct commands.
- Environment-driven dependency wiring and lifecycle cleanup.
- Docker Compose, database bootstrap, and Telegram webhook setup scripts.

## Implemented in v0.3

- **Telegram Mini App authentication** based on server-side validation of raw `Telegram.WebApp.initData`.
- HMAC-SHA-256 signature validation and `auth_date` freshness enforcement.
- Internal `User` identity separate from Telegram's user id.
- `telegram_user_id -> user_id` binding with create/update on a valid Telegram request.
- `default_relationship_id` on the user profile.
- User repository with in-memory and PostgreSQL implementations.
- Full relationship CRUD.
- Full relationship-rule CRUD.
- Ruleset version increment on mutable relationship/rule changes.
- Mini App bootstrap endpoint.
- Mini App authenticated AI endpoint that does not accept a trusted `user_id` from the client.
- Default relationship resolution inside the existing `ContextStage`.
- Telegram bot/inline requests now resolve the same internal user identity as the Mini App.
- Ownership enforcement preventing one user from selecting or using another user's relationship.
- PostgreSQL migration `migrations/0002_users_and_miniapp.sql` for existing v0.2 installations.
- Mini App YAML manifest and API documentation.

## Implemented in v0.4

- Telegram Mini App frontend (`frontend/`, React + TypeScript + Vite, `@telegram-apps/telegram-ui`).
- Bootstrap gate: users without relationships are routed to onboarding.
- Screens: Onboarding, Main (soften/decode/help-say with per-request relationship override), Relationships (create/delete/set default), Relationship details (edit, rule CRUD), Settings (ru/en override).
- Frontend consumes only `/v1/miniapp/*`; identity comes from `X-Telegram-Init-Data`.
- FastAPI serves the built frontend at `/miniapp` when `MINIAPP_STATIC_DIR` (default `frontend/dist`) exists; API routes are unaffected.
- Multi-stage `Dockerfile` (frontend build + Python runtime) and `app` service in `docker-compose.yml`.

## Current validation

- 22 backend tests pass (including `/miniapp` static hosting tests).
- Frontend typecheck/lint/Vitest/build not yet executed in this environment (Node.js unavailable).
- The test suite covers Telegram initData integrity/expiry, user creation, relationship CRUD, rule creation, default relationship resolution, tenant isolation, workflow retry/resume, OpenAI adapter contracts, Redis checkpoints, and Telegram parsing.

## Deliberately deferred

- Alembic migration framework; v0.3 ships an explicit SQL migration.
- Dedicated production moderation/safety provider.
- Persistent telemetry backend / dashboards.
- Queue/worker layer for long-running workloads.
- Billing/subscription enforcement.
- Optional first-party session tokens; v0.3 re-validates Telegram `initData` per Mini App request.

The Workflow/Stage/Skill/Tool/Artifact core remains unchanged by these additions.
