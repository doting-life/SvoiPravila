import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { runExample } from "../../../examples/typescript/basic-usage";
// @ts-expect-error -- plain JavaScript example without type declarations
import { runExample as runJsExample } from "../../../examples/javascript/fetch-example.mjs";

const FIXTURES = resolve(dirname(fileURLToPath(import.meta.url)), "../../../docs/fixtures");
const fixture = (name: string): unknown => JSON.parse(readFileSync(resolve(FIXTURES, name), "utf-8"));

function routeFetch(routes: Record<string, () => Response>) {
  const seen: string[] = [];
  const impl = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), "http://local");
    const key = `${init?.method ?? "GET"} ${url.pathname}`;
    seen.push(key);
    const route = routes[key];
    if (!route) return new Response(JSON.stringify({ detail: "Not Found" }), { status: 404 });
    return route();
  }) as typeof fetch;
  return { impl, seen };
}

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });

describe("examples/typescript/basic-usage.ts", () => {
  it("uses the default relationship and returns the softened message", async () => {
    const { impl, seen } = routeFetch({
      "GET /v1/miniapp/bootstrap": () => json(fixture("bootstrap_with_default.json")),
      "POST /v1/miniapp/assist/soften": () => json(fixture("delivery_soften.json")),
    });

    const text = await runExample({ initData: "x", fetch: impl });

    expect(text).toBe((fixture("delivery_soften.json") as { text: string }).text);
    expect(seen).toEqual(["GET /v1/miniapp/bootstrap", "POST /v1/miniapp/assist/soften"]);
  });

  it("creates a relationship and rule when the user has none", async () => {
    const { impl, seen } = routeFetch({
      "GET /v1/miniapp/bootstrap": () => json(fixture("bootstrap_without_default.json")),
      "POST /v1/miniapp/relationships": () => json(fixture("relationship.json"), 201),
      "POST /v1/miniapp/relationships/rel_7f3c2a9e/rules": () => json(fixture("rule.json"), 201),
      "POST /v1/miniapp/assist/soften": () => json(fixture("delivery_blocked.json")),
    });

    const text = await runExample({ initData: "x", fetch: impl });

    expect(text).toBe((fixture("delivery_blocked.json") as { text: string }).text);
    expect(seen).toHaveLength(4);
  });

  it("explains auth failures", async () => {
    const { impl } = routeFetch({
      "GET /v1/miniapp/bootstrap": () => json(fixture("error_503.json"), 503),
    });

    await expect(runExample({ initData: "x", fetch: impl })).resolves.toContain("not configured");
    await expect(runExample({ initData: () => null, fetch: impl })).resolves.toContain("Open the app from Telegram");
  });
});

describe("examples/javascript/fetch-example.mjs", () => {
  it("bootstraps and calls decode with plain fetch", async () => {
    const { impl, seen } = routeFetch({
      "GET /v1/miniapp/bootstrap": () => json(fixture("bootstrap_with_default.json")),
      "POST /v1/miniapp/assist/decode": () => json(fixture("delivery_decode.json")),
    });

    const result = await runJsExample("http://local/", "x", impl);

    expect(result).toMatchObject({ userId: "usr_3b1f0c5d", status: "ok" });
    expect(seen).toEqual(["GET /v1/miniapp/bootstrap", "POST /v1/miniapp/assist/decode"]);
  });

  it("surfaces backend error detail", async () => {
    const { impl } = routeFetch({
      "GET /v1/miniapp/bootstrap": () => json(fixture("error_401.json"), 401),
    });

    await expect(runJsExample("http://local", "x", impl)).rejects.toMatchObject({
      status: 401,
      detail: "Missing Telegram initData",
    });
  });
});
