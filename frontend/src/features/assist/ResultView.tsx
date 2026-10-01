import { useState } from "react";

import type { DeliveryResponse } from "../../api/types";
import type { TranslationDictionary } from "../../i18n";
import { Button, ListCell, ListSection, Notice, Stack } from "../../components/ui";
import { copyText } from "../../telegram";
import { copyableText, parseDeliveryResult } from "./results";

function Field({ label, value }: { label: string; value: string }) {
  return <ListCell subtitle={label}>{value}</ListCell>;
}

function ListField({ label, values }: { label: string; values: string[] }) {
  if (values.length === 0) {
    return null;
  }
  return (
    <ListCell subtitle={label}>
      <ul style={{ margin: 0, paddingInlineStart: 18 }}>
        {values.map((value, index) => (
          <li key={index}>{value}</li>
        ))}
      </ul>
    </ListCell>
  );
}

export function ResultView({ response, dict }: { response: DeliveryResponse; dict: TranslationDictionary }) {
  const [copied, setCopied] = useState(false);

  if (response.status === "blocked") {
    return (
      <Stack>
        <Notice tone="error">{dict.blocked}</Notice>
        {response.text ? <Notice>{response.text}</Notice> : null}
      </Stack>
    );
  }
  if (response.status === "error") {
    return (
      <Stack>
        <Notice tone="error">{dict.workflowError}</Notice>
        {response.text ? <Notice>{response.text}</Notice> : null}
      </Stack>
    );
  }

  const parsed = parseDeliveryResult(response);

  async function onCopy() {
    const ok = await copyText(copyableText(parsed, response.text));
    setCopied(ok);
  }

  return (
    <ListSection header={dict.result}>
      <div data-testid="assist-result">
        {parsed.kind === "soften" ? (
          <>
            <Field label={dict.rewrittenMessage} value={parsed.value.rewritten_message} />
            <Field label={dict.originalIntent} value={parsed.value.original_intent} />
            <Field label={dict.toneApplied} value={parsed.value.tone_applied} />
            <ListField label={dict.constraintsRespected} values={parsed.value.constraints_respected} />
          </>
        ) : null}
        {parsed.kind === "decode" ? (
          <>
            <Field label={dict.literalMeaning} value={parsed.value.literal_meaning} />
            <Field label={dict.probableIntent} value={parsed.value.probable_intent} />
            <Field label={dict.emotionalTone} value={parsed.value.emotional_tone} />
            <Field label={dict.uncertainty} value={parsed.value.uncertainty} />
            <ListField label={dict.alternativeInterpretations} values={parsed.value.alternative_interpretations} />
          </>
        ) : null}
        {parsed.kind === "help-say" ? (
          <>
            <Field label={dict.message} value={parsed.value.message} />
            <Field label={dict.tone} value={parsed.value.tone} />
            <Field label={dict.preservedIntent} value={parsed.value.preserved_intent} />
            <ListField label={dict.warnings} values={parsed.value.warnings} />
          </>
        ) : null}
        {parsed.kind === "text" ? <ListCell>{parsed.value}</ListCell> : null}
      </div>
      <Stack>
        <Button
          mode="bezeled"
          onClick={() => {
            void onCopy();
          }}
        >
          {copied ? dict.copied : dict.copy}
        </Button>
      </Stack>
    </ListSection>
  );
}
