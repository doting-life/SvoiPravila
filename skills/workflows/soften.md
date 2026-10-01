# Skill: Soften

Version: 1.0

## Objective

Перепиши сообщение так, чтобы сохранить его смысл, факты, границы и требуемую прямоту, одновременно уменьшив ненужную агрессию, обвинительный тон и формулировки, которые ухудшают вероятность конструктивного ответа.

## Required inputs

- source message;
- RelationshipContext;
- SafetyDecision instructions;
- GenerationPlan.

## Preserve

- core intent;
- factual claims;
- explicit requests;
- boundaries;
- recipient;
- intended firmness.

## Do not

- добавлять извинения, которых пользователь не выражал;
- добавлять любовь, сочувствие, благодарность или иные чувства от имени пользователя;
- менять факты;
- ослаблять принципиальную границу;
- превращать сообщение в терапевтический шаблон;
- использовать relationship rules как содержание сообщения.

## Style

Предпочитай естественную разговорную речь. Сохраняй приблизительную длину исходного сообщения, если GenerationPlan не требует другого.

## Output

Верни `SoftenResult`.
