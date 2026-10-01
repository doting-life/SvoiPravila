# Tools

## Principle

Tools — executable capabilities. LLM никогда не должен напрямую обращаться к внешнему provider SDK из workflow skill.

## Initial tool set

### `llm_generate`
Structured text generation.

### `safety_check`
Классификация запроса и policy constraints.

### `language_detect`
Определение/проверка языка.

### `relationship_context_loader`
Загрузка relationship/ruleset из PostgreSQL.

### `checkpoint_store`
Redis-backed temporary execution state.

### `trace_writer`
Запись технического RequestTrace без сырого текста сообщения.

## Base contract

Каждый tool должен объявлять:
- name;
- version;
- capability;
- provider;
- stability;
- timeout;
- retry policy;
- input schema;
- output schema;
- side effects;
- whether raw message text leaves our backend.

## Recommended execution wrapper

Provider должен реализовывать внутренний `_execute`/`execute_internal`, а общий wrapper обязан выполнять:

1. input validation;
2. dependency check;
3. timeout/retry setup;
4. idempotency handling;
5. telemetry start;
6. provider execution;
7. output validation;
8. cost/latency accounting;
9. telemetry finish.
