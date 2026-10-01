import { type FormEvent, useState } from "react";

import type { RuleBody } from "../../api/types";
import type { TranslationDictionary } from "../../i18n";
import { Button, Input, Notice, Row, Select, Stack, TextArea } from "../../components/ui";

export const SUGGESTED_RULE_TYPES = ["avoid", "prefer", "tone", "boundary", "formality"] as const;
export const RULE_TYPE_MAX_LENGTH = 64;
export const RULE_VALUE_MAX_LENGTH = 2000;
export const RULE_PRIORITY_MIN = -1000;
export const RULE_PRIORITY_MAX = 1000;

const CUSTOM = "__custom__";

type SuggestedRuleType = (typeof SUGGESTED_RULE_TYPES)[number];

function isSuggested(value: string): value is SuggestedRuleType {
  return (SUGGESTED_RULE_TYPES as readonly string[]).includes(value);
}

function suggestedLabel(type: SuggestedRuleType, dict: TranslationDictionary): string {
  switch (type) {
    case "avoid":
      return dict.ruleTypeAvoid;
    case "prefer":
      return dict.ruleTypePrefer;
    case "tone":
      return dict.ruleTypeTone;
    case "boundary":
      return dict.ruleTypeBoundary;
    case "formality":
      return dict.ruleTypeFormality;
  }
}

export function validateRule(
  body: { type: string; value: string; priority: string },
  dict: TranslationDictionary,
): { rule: RuleBody | null; error: string | null } {
  const type = body.type.trim();
  if (type.length < 1 || type.length > RULE_TYPE_MAX_LENGTH) {
    return { rule: null, error: dict.validationRuleType };
  }
  const value = body.value.trim();
  if (value.length < 1 || value.length > RULE_VALUE_MAX_LENGTH) {
    return { rule: null, error: dict.validationRuleValue };
  }
  const priorityText = body.priority.trim();
  const priority = priorityText === "" ? 0 : Number(priorityText);
  if (!Number.isInteger(priority) || priority < RULE_PRIORITY_MIN || priority > RULE_PRIORITY_MAX) {
    return { rule: null, error: dict.validationPriority };
  }
  return { rule: { type, value, priority }, error: null };
}

export function RuleForm({
  dict,
  initial,
  submitLabel,
  pending,
  onSubmit,
  onCancel,
}: {
  dict: TranslationDictionary;
  initial?: RuleBody;
  submitLabel: string;
  pending: boolean;
  onSubmit: (body: RuleBody) => void;
  onCancel?: () => void;
}) {
  const initialType = initial?.type ?? SUGGESTED_RULE_TYPES[0];
  const [selectedType, setSelectedType] = useState<string>(isSuggested(initialType) ? initialType : CUSTOM);
  const [customType, setCustomType] = useState<string>(isSuggested(initialType) ? "" : initialType);
  const [value, setValue] = useState(initial?.value ?? "");
  const [priority, setPriority] = useState(String(initial?.priority ?? 0));
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const type = selectedType === CUSTOM ? customType : selectedType;
    const result = validateRule({ type, value, priority }, dict);
    if (!result.rule) {
      setError(result.error);
      return;
    }
    setError(null);
    onSubmit(result.rule);
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <Stack>
        <Select label={dict.ruleType} value={selectedType} onChange={(event) => setSelectedType(event.target.value)}>
          {SUGGESTED_RULE_TYPES.map((type) => (
            <option key={type} value={type}>
              {suggestedLabel(type, dict)}
            </option>
          ))}
          <option value={CUSTOM}>{dict.ruleTypeCustom}</option>
        </Select>
        {selectedType === CUSTOM ? (
          <Input
            label={dict.ruleTypeCustom}
            value={customType}
            maxLength={RULE_TYPE_MAX_LENGTH}
            onChange={(event) => setCustomType(event.target.value)}
          />
        ) : null}
        <TextArea label={dict.ruleValue} value={value} onChange={(event) => setValue(event.target.value)} />
        <Input
          label={dict.rulePriority}
          type="number"
          inputMode="numeric"
          min={RULE_PRIORITY_MIN}
          max={RULE_PRIORITY_MAX}
          step={1}
          value={priority}
          onChange={(event) => setPriority(event.target.value)}
        />
        {error ? <Notice tone="error">{error}</Notice> : null}
        <Row>
          <Button type="submit" loading={pending} disabled={pending}>
            {submitLabel}
          </Button>
          {onCancel ? (
            <Button mode="bezeled" onClick={onCancel}>
              {dict.cancel}
            </Button>
          ) : null}
        </Row>
      </Stack>
    </form>
  );
}
