# Output Contract Skill

## Purpose

Верни только данные, требуемые output schema текущего workflow.

## Rules

1. Не добавляй поля вне schema.
2. Не помещай комментарии вокруг structured output.
3. Используй язык исходного пользовательского запроса, если GenerationPlan не требует другого.
4. Не добавляй markdown formatting внутрь готового сообщения без явного запроса.
5. Если требуемый факт неизвестен, отрази uncertainty вместо выдумывания.
