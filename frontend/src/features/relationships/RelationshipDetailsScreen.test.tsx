import { fireEvent, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { BootstrapResponse } from "../../api/types";
import { makeBootstrap, makeRelationship } from "../../test/fixtures";
import { renderRoutes, resetUiStore } from "../../test/render";
import { testServer } from "../../test/setup";
import { RelationshipDetailsScreen } from "./RelationshipDetailsScreen";

vi.mock("../../telegram", () => ({
  getLaunchLanguage: () => "en",
  getRawInitData: () => "test_init_data",
  initTelegram: () => undefined,
  attachBackButton: () => () => undefined,
  copyText: async () => true,
}));

const REL = makeRelationship({
  relationship_id: "rel-1",
  aliases: ["Alex"],
  relation_type: "friend",
  rules: [{ id: 7, type: "tone", value: "Be calm", priority: 5, created_at: null }],
});

function mockBootstrap(initial: BootstrapResponse) {
  const state = { current: initial };
  testServer.use(http.get("/v1/miniapp/bootstrap", () => HttpResponse.json(state.current)));
  return state;
}

function renderDetails(id = "rel-1") {
  return renderRoutes(
    {
      "/relationships/:relationshipId": <RelationshipDetailsScreen />,
      "/relationships": <div>relationships-list</div>,
    },
    `/relationships/${id}`,
  );
}

describe("RelationshipDetailsScreen", () => {
  beforeEach(() => {
    resetUiStore();
  });

  it("shows not found for an unknown relationship", async () => {
    mockBootstrap(makeBootstrap([REL], "rel-1"));
    renderDetails("missing");
    expect(await screen.findByText("Relationship not found")).toBeInTheDocument();
  });

  it("edits relation type and aliases", async () => {
    mockBootstrap(makeBootstrap([REL], "rel-1"));
    const bodies: unknown[] = [];
    testServer.use(
      http.patch("/v1/miniapp/relationships/:relationshipId", async ({ request }) => {
        bodies.push(await request.json());
        return HttpResponse.json(REL);
      }),
    );

    renderDetails();
    fireEvent.change(await screen.findByLabelText("Relation type"), { target: { value: "partner" } });
    fireEvent.change(screen.getByLabelText("Names (comma-separated)"), { target: { value: "Alex, Al" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(bodies).toEqual([{ relation_type: "partner", aliases: ["Alex", "Al"] }]));
  });

  it("does not allow clearing an existing relation type", async () => {
    mockBootstrap(makeBootstrap([REL], "rel-1"));
    renderDetails();
    fireEvent.change(await screen.findByLabelText("Relation type"), { target: { value: "  " } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(await screen.findByText("Relation type is required")).toBeInTheDocument();
  });

  it("adds a rule with a custom type and validates ranges", async () => {
    mockBootstrap(makeBootstrap([REL], "rel-1"));
    const bodies: unknown[] = [];
    testServer.use(
      http.post("/v1/miniapp/relationships/:relationshipId/rules", async ({ request }) => {
        bodies.push(await request.json());
        return HttpResponse.json({ id: 8, type: "topic", value: "No politics", priority: 10 }, { status: 201 });
      }),
    );

    renderDetails();
    fireEvent.click(await screen.findByRole("button", { name: "Add rule" }));
    fireEvent.change(screen.getByLabelText("Rule type"), { target: { value: "__custom__" } });
    fireEvent.change(screen.getByLabelText("Custom type"), { target: { value: "topic" } });
    fireEvent.change(screen.getByLabelText("Rule text"), { target: { value: "No politics" } });
    fireEvent.change(screen.getByLabelText("Priority"), { target: { value: "5000" } });
    fireEvent.click(screen.getByRole("button", { name: "Add rule" }));
    expect(await screen.findByText("Priority must be an integer from -1000 to 1000")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Priority"), { target: { value: "10" } });
    fireEvent.click(screen.getByRole("button", { name: "Add rule" }));
    await waitFor(() => expect(bodies).toEqual([{ type: "topic", value: "No politics", priority: 10 }]));
  });

  it("edits and deletes an existing rule", async () => {
    mockBootstrap(makeBootstrap([REL], "rel-1"));
    const updates: unknown[] = [];
    const deletes: string[] = [];
    testServer.use(
      http.put("/v1/miniapp/relationships/:relationshipId/rules/:ruleId", async ({ request, params }) => {
        updates.push({ id: params.ruleId, body: await request.json() });
        return HttpResponse.json({ id: 7, type: "tone", value: "Be kind", priority: 5 });
      }),
      http.delete("/v1/miniapp/relationships/:relationshipId/rules/:ruleId", ({ params }) => {
        deletes.push(String(params.ruleId));
        return new HttpResponse(null, { status: 204 });
      }),
    );

    renderDetails();
    fireEvent.click(await screen.findByRole("button", { name: "Edit: Be calm" }));
    fireEvent.change(screen.getByLabelText("Rule text"), { target: { value: "Be kind" } });
    const saveButtons = screen.getAllByRole("button", { name: "Save" });
    fireEvent.click(saveButtons[saveButtons.length - 1]!);
    await waitFor(() => expect(updates).toEqual([{ id: "7", body: { type: "tone", value: "Be kind", priority: 5 } }]));

    fireEvent.click(await screen.findByRole("button", { name: "Delete: Be calm" }));
    fireEvent.click(await screen.findByRole("button", { name: "Delete" }));
    await waitFor(() => expect(deletes).toEqual(["7"]));
  });

  it("shows not found when a rule operation returns 404", async () => {
    mockBootstrap(makeBootstrap([REL], "rel-1"));
    testServer.use(
      http.delete("/v1/miniapp/relationships/:relationshipId/rules/:ruleId", () =>
        HttpResponse.json({ detail: "Rule not found" }, { status: 404 }),
      ),
    );
    renderDetails();
    fireEvent.click(await screen.findByRole("button", { name: "Delete: Be calm" }));
    fireEvent.click(await screen.findByRole("button", { name: "Delete" }));
    expect(await screen.findByText("Not found.")).toBeInTheDocument();
  });
});
