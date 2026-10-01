# Architecture

## 1. Цель

«Свои Правила» — AI-сервис для помощи в межличностной коммуникации. Пользователь настраивает правила общения для конкретных отношений, а затем вызывает короткие AI-workflows из Telegram / Mini App.

MVP поддерживает три сценария:

- **Смягчить** — сохранить смысл, снизив ненужную агрессию или резкость.
- **Расшифровать** — объяснить возможный буквальный смысл, намерение и эмоциональный тон чужого сообщения без выдачи догадок за факты.
- **Помоги сказать** — превратить намерение пользователя в готовое сообщение с учётом правил конкретных отношений.

## 2. Архитектурный принцип

LLM не является workflow engine.

Python-код отвечает за:
- выбор workflow;
- порядок stages;
- загрузку входных данных;
- schema validation;
- policy enforcement;
- retries/timeouts;
- checkpoint/resume;
- provider access;
- observability;
- privacy boundaries.

LLM отвечает за:
- семантический анализ;
- интерпретацию контекста;
- план преобразования;
- генерацию текста;
- качественные решения внутри разрешённой стадии.

## 3. High-level flow

```text
Telegram Bot / Mini App
          |
          v
Identity / Auth Adapter
  Mini App: verified initData
  Bot: verified Telegram update
          |
          v
Internal User + Relationship selection
          |
          v
Workflow Registry
          |
          v
Workflow Engine (Python)
          |
          +--> Receive Stage
          +--> Safety Stage
          +--> Context Stage
          +--> Plan Stage
          +--> Generate Stage
          +--> Validate Stage
          +--> Deliver Stage
          |
          v
Response Adapter
          |
          v
Telegram / Mini App
```

## 4. Core entities

### User
Внутренняя identity сущность. `telegram_user_id` является внешним идентификатором, а workflows работают с внутренним `user_id`. User хранит `default_relationship_id`.

### Workflow
Определяет конечный пользовательский сценарий и последовательность stages.

### Stage
Детерминированная единица orchestration. Stage получает typed artifacts и создаёт новый typed artifact.

### Skill
Версионируемая инструкция для LLM. Skill описывает цель, ограничения, reasoning guidance и output contract.

### Tool
Детерминированный executable capability: LLM provider, safety checker, language detector, persistence adapter и т.д.

### Artifact
Структурированный typed результат стадии. Между stages передаются artifacts, а не свободный текст.

### Checkpoint
Краткоживущий снимок выполнения запроса, позволяющий корректно сделать retry/resume.

## 5. Data flow

```text
MessageRequest
    |
    v
SafetyDecision
    |
    v
RelationshipContext
    |
    v
GenerationPlan
    |
    v
WorkflowResult
    |
    v
ValidationResult
    |
    v
DeliveryResponse
```

Каждый artifact должен иметь:
- `version`;
- `request_id`;
- собственный schema contract;
- timestamps/metadata при необходимости.

## 6. Persistent vs ephemeral state

### PostgreSQL
Храним:
- users;
- relationships;
- rules;
- preferences;
- ruleset versions;
- feature flags / experiments;
- feedback;
- technical traces без raw message text.

### Redis
Храним временно:
- request state;
- current stage;
- intermediate artifacts;
- retry counters;
- idempotency keys;
- short-lived provider state.

Рекомендуемый TTL для request state: 5–30 минут.

### Raw message content
По умолчанию не сохраняется в постоянной БД. Допускается краткоживущее хранение только для выполнения текущего запроса.

## 7. Recommended Python boundaries

```text
app/
  api/
    telegram/
    miniapp/

  workflows/
    engine.py
    registry.py
    soften.py
    decode.py
    help_say.py

  stages/
    receive.py
    safety.py
    context.py
    planning.py
    generation.py
    validation.py
    delivery.py

  skills/
    loader.py

  artifacts/
    request.py
    safety.py
    context.py
    plan.py
    response.py
    validation.py

  tools/
    base.py
    registry.py
    llm/
    safety/
    language/

  repositories/
    users.py
    relationships.py
    rules.py

  checkpoints/
    redis_store.py

  observability/
    trace.py
    metrics.py
    cost.py

  domain/
```

## 8. Hard rules

1. Stage order is controlled by code, not LLM.
2. A stage cannot consume artifacts not declared in its workflow contract.
3. LLM output must pass typed validation before advancing.
4. Safety constraints cannot be weakened by a workflow skill.
5. Relationship rules are user state, not conversation memory.
6. Mini App never supplies a trusted `user_id`; identity is derived from verified Telegram `initData`.
7. Every relationship access is owner-scoped.
8. Raw user message content is not persisted by default.
9. Provider/model choice is observable and traceable.
10. Skills are versioned executable specifications and must be testable.
11. Fallbacks may not silently change the semantic promise of the workflow.
12. All retries must be idempotent where technically possible.

## Mini App frontend (v0.4)

`frontend/` is a thin client: React screens -> React Query hooks -> `api/miniapp.ts` -> `/v1/miniapp/*`. Telegram SDK access is isolated in `frontend/src/telegram`, UI kit access in `frontend/src/components/ui`. No workflow logic, identity, or ownership decisions live in the frontend. FastAPI optionally mounts the built bundle at `/miniapp`.

