import { getRawInitData } from "../telegram";

export class ApiError extends Error {
  readonly status: number;

  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function getApiBase(): string {
  const base = import.meta.env.VITE_API_BASE?.trim() ?? "";
  if (!base) {
    return "";
  }
  return base.replace(/\/$/, "");
}

export function buildApiUrl(path: string): string {
  if (!path.startsWith("/")) {
    throw new Error("API path must start with '/' to stay absolute");
  }
  return `${getApiBase()}${path}`;
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
};

export async function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const initData = getRawInitData();
  if (!initData) {
    throw new ApiError(401, "Missing Telegram initData");
  }

  const response = await fetch(buildApiUrl(path), {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": initData,
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const payload = (await response.json().catch(() => null)) as { detail?: unknown } | null;
  if (!response.ok) {
    const detail = typeof payload?.detail === "string" ? payload.detail : "Request failed";
    throw new ApiError(response.status, detail);
  }

  return payload as T;
}
