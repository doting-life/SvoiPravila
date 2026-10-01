# Observability

## RequestTrace

Постоянный технический trace не должен содержать raw message text.

Рекомендуемые поля:
- request_id;
- user_id pseudonymous/internal;
- workflow;
- skill_version;
- ruleset_version;
- provider;
- model;
- safety_status;
- fallback_used;
- retry_count;
- latency_ms;
- tokens_in;
- tokens_out;
- cost_usd;
- validation_status;
- user_feedback;
- created_at.

## Metrics

### Product
- workflow usage;
- copy rate;
- send rate;
- thumbs up/down;
- retry/rephrase rate.

### Quality
- schema retry rate;
- validation failure rate;
- safety intervention rate;
- relationship-rule violation rate.

### Runtime
- p50/p95 latency;
- provider errors;
- timeout rate;
- token usage;
- cost/request.

## Experiments

A/B tests должны назначать:
- skill_version;
- model config;
- generation settings;
- validator config.

Нельзя смешивать несколько неизвестных изменений в одном эксперименте без отдельного attribution strategy.
