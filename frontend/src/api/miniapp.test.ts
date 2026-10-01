import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { buildApiUrl, requestJson } from "./client";
import { miniAppApi } from "./miniapp";
import { testServer } from "../test/setup";

vi.mock("../telegram", () => ({
  getRawInitData: () => "test_init_data",
}));

describe("miniAppApi", () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
  });

  it("builds absolute backend urls and never prefixes with /miniapp/", () => {
    expect(buildApiUrl("/v1/miniapp/bootstrap")).toBe("/v1/miniapp/bootstrap");
    expect(buildApiUrl("/v1/miniapp/bootstrap").startsWith("/miniapp/")).toBe(false);

    vi.stubEnv("VITE_API_BASE", "https://example.com");
    expect(buildApiUrl("/v1/miniapp/bootstrap")).toBe("https://example.com/v1/miniapp/bootstrap");
  });

  it("sends Telegram initData header and strict body", async () => {
    testServer.use(
      http.post("/v1/miniapp/relationships", async ({ request }) => {
        expect(request.headers.get("X-Telegram-Init-Data")).toBe("test_init_data");
        const body = (await request.json()) as Record<string, unknown>;
        expect(body).toEqual({
          relation_type: "friend",
          aliases: ["Alex"],
          communication_style: { tone: "gentle" },
          set_as_default: true,
        });

        return HttpResponse.json({
          relationship_id: "r1",
          relation_type: "friend",
          aliases: ["Alex"],
          communication_style: { tone: "gentle" },
          ruleset_version: 0,
          rules: [],
        });
      }),
    );

    const relationship = await miniAppApi.createRelationship({
      relation_type: "friend",
      aliases: ["Alex"],
      communication_style: { tone: "gentle" },
      set_as_default: true,
    });

    expect(relationship.relationship_id).toBe("r1");
  });

  it("handles 204 responses", async () => {
    testServer.use(
      http.delete("/v1/miniapp/relationships/:relationshipId", () => new HttpResponse(null, { status: 204 })),
    );

    await expect(miniAppApi.deleteRelationship("r1")).resolves.toBeUndefined();
  });

  it("maps backend error statuses and details", async () => {
    testServer.use(
      http.get("/v1/miniapp/bootstrap", () => HttpResponse.json({ detail: "unauthorized" }, { status: 401 })),
    );

    await expect(miniAppApi.bootstrap()).rejects.toMatchObject({ status: 401, detail: "unauthorized" });

    testServer.use(
      http.get("/v1/miniapp/bootstrap", () => HttpResponse.json({ detail: "not found" }, { status: 404 })),
    );

    await expect(miniAppApi.bootstrap()).rejects.toMatchObject({ status: 404, detail: "not found" });

    testServer.use(
      http.get("/v1/miniapp/bootstrap", () => HttpResponse.json({ detail: "not configured" }, { status: 503 })),
    );

    await expect(miniAppApi.bootstrap()).rejects.toMatchObject({ status: 503, detail: "not configured" });
  });

  it("calls all workflow assist endpoints", async () => {
    const workflows = new Set(["soften", "decode", "help-say"]);

    testServer.use(
      http.post("/v1/miniapp/assist/:workflow", async ({ params, request }) => {
        expect(workflows.has(String(params.workflow))).toBe(true);
        const body = (await request.json()) as Record<string, unknown>;
        expect(body).toEqual({ text: "hello", language: "ru" });
        return HttpResponse.json({
          version: "1.0",
          request_id: "11111111-1111-1111-1111-111111111111",
          workflow: params.workflow,
          status: "ok",
          text: "ok",
          structured_result: null,
        });
      }),
    );

    for (const workflow of workflows) {
      const result = await miniAppApi.assist(workflow as "soften" | "decode" | "help-say", {
        text: "hello",
        language: "ru",
      });
      expect(result.status).toBe("ok");
    }
  });

  it("throws for relative API path", async () => {
    await expect(requestJson("v1/miniapp/bootstrap")).rejects.toThrow("API path must start with '/'");
  });
});
