import type { DeliveryResponse, WorkflowName } from "./types";
import { workflowNameValues } from "./types";
import { MiniAppApiError } from "./errors";

// `DeliveryResponse.structured_result` is an open object in the OpenAPI
// contract. These shapes mirror the backend workflow artifacts
// (SoftenResult, DecodeResult, HelpSayResult) as serialized by the API.

type ArtifactBase = {
  version: string;
  request_id: string;
};

export type SoftenResult = ArtifactBase & {
  original_intent: string;
  rewritten_message: string;
  tone_applied: string;
  constraints_respected: string[];
};

export type DecodeResult = ArtifactBase & {
  literal_meaning: string;
  probable_intent: string;
  emotional_tone: string;
  uncertainty: string;
  alternative_interpretations: string[];
};

export type HelpSayResult = ArtifactBase & {
  message: string;
  tone: string;
  preserved_intent: string;
  warnings: string[];
};

export type WorkflowResultMap = {
  soften: SoftenResult;
  decode: DecodeResult;
  "help-say": HelpSayResult;
};

const DELIVERY_STATUSES = ["ok", "blocked", "error"] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isString(value: unknown): value is string {
  return typeof value === "string";
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(isString);
}

function hasStrings(value: Record<string, unknown>, keys: string[]): boolean {
  return keys.every((key) => isString(value[key]));
}

export function isWorkflowName(value: unknown): value is WorkflowName {
  return isString(value) && (workflowNameValues as readonly string[]).includes(value);
}

export function isDeliveryResponse(value: unknown): value is DeliveryResponse {
  return (
    isRecord(value) &&
    hasStrings(value, ["version", "request_id", "text"]) &&
    isWorkflowName(value.workflow) &&
    (DELIVERY_STATUSES as readonly unknown[]).includes(value.status) &&
    (value.structured_result === null || isRecord(value.structured_result))
  );
}

export function isSoftenResult(value: unknown): value is SoftenResult {
  return (
    isRecord(value) &&
    hasStrings(value, ["version", "request_id", "original_intent", "rewritten_message", "tone_applied"]) &&
    isStringArray(value.constraints_respected)
  );
}

export function isDecodeResult(value: unknown): value is DecodeResult {
  return (
    isRecord(value) &&
    hasStrings(value, ["version", "request_id", "literal_meaning", "probable_intent", "emotional_tone", "uncertainty"]) &&
    isStringArray(value.alternative_interpretations)
  );
}

export function isHelpSayResult(value: unknown): value is HelpSayResult {
  return (
    isRecord(value) &&
    hasStrings(value, ["version", "request_id", "message", "tone", "preserved_intent"]) &&
    isStringArray(value.warnings)
  );
}

const RESULT_GUARDS: { [K in WorkflowName]: (value: unknown) => value is WorkflowResultMap[K] } = {
  soften: isSoftenResult,
  decode: isDecodeResult,
  "help-say": isHelpSayResult,
};

/**
 * Returns the typed structured result for an `ok` delivery, or null when the
 * response is blocked/error or the payload does not match the workflow shape.
 */
export function getStructuredResult<W extends WorkflowName>(
  response: DeliveryResponse & { workflow: W },
): WorkflowResultMap[W] | null {
  if (response.status !== "ok") return null;
  const guard = RESULT_GUARDS[response.workflow] as (value: unknown) => value is WorkflowResultMap[W];
  return guard(response.structured_result) ? response.structured_result : null;
}

export function isMiniAppApiError(value: unknown): value is MiniAppApiError {
  return value instanceof MiniAppApiError;
}
