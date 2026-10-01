# Project Context

## Product identity

«Свои Правила» помогает пользователю формулировать и интерпретировать сообщения в рамках конкретных отношений и заранее определённых правил общения.

## MVP surfaces

### Telegram Inline / Bot
Основной execution surface для быстрых запросов.

### Mini App
Authenticated control plane. `Telegram.WebApp.initData` валидируется backend-ом; Telegram identity связывается с внутренним `User`. Mini App отвечает за:
- отношений;
- правил;
- tone preferences;
- aliases;
- onboarding;
- settings;
- feedback/history metadata без обязательного хранения сырого текста сообщений.

## Current workflows

| Workflow | User intent | Output |
|---|---|---|
| `soften` | Смягчить сообщение | готовая переформулировка |
| `decode` | Понять чужое сообщение | структурированная интерпретация |
| `help-say` | Сформулировать своё намерение | готовое сообщение |

## Context model

Система не обязана хранить историю переписки пользователя, чтобы быть персонализированной.

Главный постоянный контекст:
- кто адресат;
- тип отношений;
- правила;
- предпочтительный стиль;
- разрешённая степень прямоты;
- индивидуальные ограничения;
- версия ruleset.

## Architectural source of truth

- `docs/ARCHITECTURE.md` — общая архитектура.
- `docs/WORKFLOWS.md` — pipeline semantics.
- `docs/ARTIFACTS.md` — typed artifacts.
- `docs/SKILLS.md` — skill model.
- `docs/TOOLS.md` — executable capabilities.
- `docs/CHECKPOINTS.md` — execution state and retries.
- `docs/OBSERVABILITY.md` — request tracing, cost, quality.
- `docs/SECURITY_PRIVACY.md` — privacy/security boundaries.
- `docs/MINIAPP_API.md` — Telegram Mini App auth, users, relationships and rules API.
- `config/**/*.yaml` — machine-readable manifests.
