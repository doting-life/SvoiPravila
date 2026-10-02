import { MISSING_INIT_DATA_DETAIL, MiniAppApiError, errorFromResponse } from "./errors";
import type {
  AuthResponse,
  BootstrapResponse,
  DeliveryResponse,
  MiniAppAssistBody,
  RelationshipCreateBody,
  RelationshipRule,
  RelationshipUpdateBody,
  RelationshipView,
  RuleBody,
  UserView,
  WorkflowName,
} from "./types";

export const MINIAPP_PREFIX = "/v1/miniapp";
export const INIT_DATA_HEADER = "X-Telegram-Init-Data";

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export type InitDataProvider = () => string | null | undefined | Promise<string | null | undefined>;

export type MiniAppClientOptions = {
  /** Raw Telegram `initData` string, or a function returning it (sync or async). */
  initData: string | InitDataProvider;
  /** Backend origin, e.g. "https://api.example.com". Empty string = same origin. */
  baseUrl?: string | (() => string);
  /** Custom fetch implementation (defaults to globalThis.fetch). */
  fetch?: typeof fetch;
};

export type RequestOptions = {
  method?: HttpMethod;
  body?: unknown;
  signal?: AbortSignal;
};

export type MiniAppClient = {
  /** Low-level request helper. `path` must be absolute (start with "/"). */
  request: <T>(path: string, options?: RequestOptions) => Promise<T>;
  buildUrl: (path: string) => string;
  auth: () => Promise<AuthResponse>;
  bootstrap: () => Promise<BootstrapResponse>;
  listRelationships: () => Promise<RelationshipView[]>;
  createRelationship: (body: RelationshipCreateBody) => Promise<RelationshipView>;
  updateRelationship: (relationshipId: string, body: RelationshipUpdateBody) => Promise<RelationshipView>;
  deleteRelationship: (relationshipId: string) => Promise<void>;
  setDefaultRelationship: (relationshipId: string) => Promise<UserView>;
  addRule: (relationshipId: string, body: RuleBody) => Promise<RelationshipRule>;
  updateRule: (relationshipId: string, ruleId: number, body: RuleBody) => Promise<RelationshipRule>;
  deleteRule: (relationshipId: string, ruleId: number) => Promise<void>;
  assist: <W extends WorkflowName>(
    workflow: W,
    body: MiniAppAssistBody,
  ) => Promise<DeliveryResponse & { workflow: W }>;
};

function normalizeBase(base: string): string {
  return base.trim().replace(/\/+$/, "");
}

const seg = encodeURIComponent;

export function createMiniAppClient(options: MiniAppClientOptions): MiniAppClient {
  const resolveBase = (): string =>
    normalizeBase(typeof options.baseUrl === "function" ? options.baseUrl() : (options.baseUrl ?? ""));

  const resolveInitData = async (): Promise<string | null | undefined> =>
    typeof options.initData === "function" ? options.initData() : options.initData;

  const buildUrl = (path: string): string => {
    if (!path.startsWith("/")) {
      throw new Error("API path must start with '/' to stay absolute");
    }
    return `${resolveBase()}${path}`;
  };

  async function request<T>(path: string, requestOptions: RequestOptions = {}): Promise<T> {
    const url = buildUrl(path);
    const initData = await resolveInitData();
    if (!initData) {
      throw new MiniAppApiError(401, MISSING_INIT_DATA_DETAIL);
    }

    const fetchImpl = options.fetch ?? globalThis.fetch;
    const response = await fetchImpl(url, {
      method: requestOptions.method ?? "GET",
      headers: {
        "Content-Type": "application/json",
        [INIT_DATA_HEADER]: initData,
      },
      body: requestOptions.body === undefined ? undefined : JSON.stringify(requestOptions.body),
      signal: requestOptions.signal,
    });

    if (response.status === 204) {
      return undefined as T;
    }

    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      throw errorFromResponse(response.status, payload);
    }
    return payload as T;
  }

  const p = MINIAPP_PREFIX;

  return {
    request,
    buildUrl,
    auth: () => request<AuthResponse>(`${p}/auth`, { method: "POST" }),
    bootstrap: () => request<BootstrapResponse>(`${p}/bootstrap`),
    listRelationships: () => request<RelationshipView[]>(`${p}/relationships`),
    createRelationship: (body) => request<RelationshipView>(`${p}/relationships`, { method: "POST", body }),
    updateRelationship: (relationshipId, body) =>
      request<RelationshipView>(`${p}/relationships/${seg(relationshipId)}`, { method: "PATCH", body }),
    deleteRelationship: (relationshipId) =>
      request<void>(`${p}/relationships/${seg(relationshipId)}`, { method: "DELETE" }),
    setDefaultRelationship: (relationshipId) =>
      request<UserView>(`${p}/me/default-relationship/${seg(relationshipId)}`, { method: "PUT" }),
    addRule: (relationshipId, body) =>
      request<RelationshipRule>(`${p}/relationships/${seg(relationshipId)}/rules`, { method: "POST", body }),
    updateRule: (relationshipId, ruleId, body) =>
      request<RelationshipRule>(`${p}/relationships/${seg(relationshipId)}/rules/${ruleId}`, {
        method: "PUT",
        body,
      }),
    deleteRule: (relationshipId, ruleId) =>
      request<void>(`${p}/relationships/${seg(relationshipId)}/rules/${ruleId}`, { method: "DELETE" }),
    assist: (workflow, body) =>
      request<DeliveryResponse & { workflow: typeof workflow }>(`${p}/assist/${seg(workflow)}`, {
        method: "POST",
        body,
      }),
  };
}
