import type { DeliveryResponse } from "../../api/types";

export type SoftenResultView = {
  original_intent: string;
  rewritten_message: string;
  tone_applied: string;
  constraints_respected: string[];
};

export type DecodeResultView = {
  literal_meaning: string;
  probable_intent: string;
  emotional_tone: string;
  uncertainty: string;
  alternative_interpretations: string[];
};

export type HelpSayResultView = {
  message: string;
  tone: string;
  preserved_intent: string;
  warnings: string[];
};

export type ParsedResult =
  | { kind: "soften"; value: SoftenResultView }
  | { kind: "decode"; value: DecodeResultView }
  | { kind: "help-say"; value: HelpSayResultView }
  | { kind: "text"; value: string };

function isString(value: unknown): value is string {
  return typeof value === "string";
}

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter(isString) : [];
}

export function parseDeliveryResult(response: DeliveryResponse): ParsedResult {
  const data = response.structured_result;
  if (data) {
    if (
      response.workflow === "soften" &&
      isString(data.rewritten_message) &&
      isString(data.original_intent) &&
      isString(data.tone_applied)
    ) {
      return {
        kind: "soften",
        value: {
          original_intent: data.original_intent,
          rewritten_message: data.rewritten_message,
          tone_applied: data.tone_applied,
          constraints_respected: stringList(data.constraints_respected),
        },
      };
    }
    if (
      response.workflow === "decode" &&
      isString(data.literal_meaning) &&
      isString(data.probable_intent) &&
      isString(data.emotional_tone) &&
      isString(data.uncertainty)
    ) {
      return {
        kind: "decode",
        value: {
          literal_meaning: data.literal_meaning,
          probable_intent: data.probable_intent,
          emotional_tone: data.emotional_tone,
          uncertainty: data.uncertainty,
          alternative_interpretations: stringList(data.alternative_interpretations),
        },
      };
    }
    if (
      response.workflow === "help-say" &&
      isString(data.message) &&
      isString(data.tone) &&
      isString(data.preserved_intent)
    ) {
      return {
        kind: "help-say",
        value: {
          message: data.message,
          tone: data.tone,
          preserved_intent: data.preserved_intent,
          warnings: stringList(data.warnings),
        },
      };
    }
  }
  return { kind: "text", value: response.text };
}

export function copyableText(parsed: ParsedResult, fallbackText: string): string {
  switch (parsed.kind) {
    case "soften":
      return parsed.value.rewritten_message;
    case "help-say":
      return parsed.value.message;
    case "decode":
      return fallbackText;
    case "text":
      return parsed.value;
  }
}
