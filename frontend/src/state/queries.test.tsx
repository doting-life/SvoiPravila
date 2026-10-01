import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { type PropsWithChildren } from "react";
import { describe, expect, it, vi } from "vitest";

import { testServer } from "../test/setup";
import { useBootstrapQuery, useCreateRelationshipMutation } from "./queries";

vi.mock("../telegram", () => ({
  getRawInitData: () => "test_init_data",
}));

function createWrapper() {
  const queryClient = new QueryClient();
  return function Wrapper({ children }: PropsWithChildren) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe("query hooks", () => {
  it("invalidates bootstrap after relationship creation", async () => {
    let bootstrapHits = 0;
    testServer.use(
      http.get("/v1/miniapp/bootstrap", () => {
        bootstrapHits += 1;
        return HttpResponse.json({
          user: {
            user_id: "u1",
            telegram_user_id: 1,
            first_name: "A",
            last_name: null,
            username: null,
            language_code: "ru",
            default_relationship_id: null,
          },
          relationships: [],
        });
      }),
      http.post("/v1/miniapp/relationships", () =>
        HttpResponse.json(
          {
            relationship_id: "r1",
            relation_type: "friend",
            aliases: [],
            communication_style: {},
            ruleset_version: 0,
            rules: [],
          },
          { status: 201 },
        ),
      ),
    );
    const wrapper

    const { result: bootstrap } = renderHook(() => useBootstrapQuery(), { wrapper });
    await waitFor(() => expect(bootstrap.current.isSuccess).toBe(true));
    expect(bootstrapHits).toBe(1);

    const { result: mutation } = renderHook(() => useCreateRelationshipMutation(), { wrapper });
    act(() => {
      mutation.current.mutate({ relation_type: "friend", aliases: [], communication_style: {} });
    });

    await waitFor(() => expect(mutation.current.isSuccess).toBe(true));
    await waitFor(() => expect(bootstrapHits).toBeGreaterThan(1));
  });
});
