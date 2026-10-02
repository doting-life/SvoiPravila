import { createMiniAppClient, MiniAppApiError, type RequestOptions } from "@svoi-pravila/miniapp-client";

import { getRawInitData } from "../telegram";

export { MiniAppApiError as ApiError };

export const apiClient = createMiniAppClient({
  initData: () => getRawInitData(),
  baseUrl: () => import.meta.env.VITE_API_BASE ?? "",
});

export function buildApiUrl(path: string): string {
  return apiClient.buildUrl(path);
}

export function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  return apiClient.request<T>(path, options);
}
