# Workflows

## Common stage model

Все MVP workflows используют общий skeleton:

```text
receive -> safety -> context -> plan -> generate -> validate -> deliver
```

### receive
Нормализует входной запрос и создаёт `MessageRequest`.

### safety
Создаёт `SafetyDecision`. Может разрешить запрос, добавить ограничения или остановить выполнение.

### context
Загружает relationship state и формирует `RelationshipContext`.

### plan
Создаёт `GenerationPlan`: цель преобразования, tone, constraints и skill version.

### generate
Запускает соответствующий workflow skill через LLM tool и получает typed result.

### validate
Проверяет schema, language, semantic invariants и policy constraints.

### deliver
Формирует финальный response DTO для Telegram/Mini App.

## Workflow: soften

### Promise
Сохранить исходный смысл пользователя, уменьшив ненужную враждебность/резкость и соблюдая relationship rules.

### Must preserve
- core intent;
- factual claims;
- requested boundaries;
- requested firmness unless она сама является источником запрещённой формулировки.

### Must not
- выдумывать чувства пользователя;
- превращать просьбу/границу в извинение;
- добавлять новые факты;
- делать текст искусственно терапевтическим;
- менять адресата.

## Workflow: decode

### Promise
Дать структурированную, осторожную интерпретацию чужого сообщения.

### Must distinguish
- literal meaning;
- likely intent;
- emotional tone;
- uncertainty.

### Must not
- утверждать мотив как факт;
- диагностировать человека;
- приписывать скрытые намерения без оговорки;
- выдавать один вариант интерпретации как единственно возможный.

## Workflow: help-say

### Promise
Преобразовать цель пользователя в готовое сообщение адресату.

### Must preserve
- desired outcome;
- non-negotiable facts;
- relationship rules;
- desired level of directness.

### Must not
- вводить новые обязательства;
- добавлять обещания от имени пользователя;
- сглаживать принципиальную границу без запроса пользователя;
- добавлять ложные эмоции.
