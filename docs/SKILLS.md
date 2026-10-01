# Skills

## Definition

Skill — версионируемая executable specification для LLM. Skill не управляет порядком stages и не имеет права обходить workflow engine.

## Skill layers

### Core skills
Общие для всех workflows:
- safety behavior;
- relationship rule interpretation;
- output contract.

### Workflow skills
Специфические сценарии:
- soften;
- decode;
- help-say.

## Skill contract

Каждый skill должен иметь:
- name;
- version;
- objective;
- required inputs;
- constraints;
- reasoning guidance;
- output schema;
- examples/anti-examples при необходимости;
- compatible workflows.

## Versioning

Изменение поведения skill требует новой версии.

Пример:
- `soften@1.0`
- `soften@1.1`

Request trace должен содержать использованную версию.

## Testing

Для skills нужны:
- golden input/output cases;
- invariant tests;
- regression cases;
- safety cases;
- relationship-rule adherence cases.
