import { fireEvent, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { BootstrapResponse } from "../../api/types";
import { makeBootstrap, makeRelationship, makeUser } from "../../test/fixtures";
import { renderRoutes, resetUiStore } from "../../test/render";
import { testServer } from "../../test/setup";
import { useUiStore } from "../../state/uiStore";
import { RelationshipsScreen } from "./RelationshipsScreen";

vi.mock("../../telegram", () => ({
  getLaunchLanguage: () => "en",
  getRawInitData: () => "test_init_data",
  initTelegram: () => undefined,
  attachBackButton: () => () => undefined,
  copyText: async () => true,
}));

const REL_1 = makeRelationship({ relationship_id: "rel-1", aliases: ["Alex"], relation_type: "friend" });
const REL_2 = makeRelationship({ relationship_id: "rel-2", aliases: ["Boss"], relation_type: "manager" });

function mockBootstrap(initial: BootstrapResponse) {
  const state = { current: initial };
  testServer.use(http.get("/v1/miniapp/bootstrap", () => HttpResponse.json(state.current)));
  return state;
}

function renderScreen() {
  return renderRoutes(
    {
      "/relationships": <RelationshipsScreen />,
      "/relationships/:relationshipId": <div>details-screen</div>,
    },
    "/relationships",
  );
}

describe("RelationshipsScreen", () => {
  beforeEach(() => {
    resetUiStore();
  });

  it("shows default badge and no-default state after deleting the default without auto-selection", async () => {
    const state = mockBootstrap(makeBootstrap([REL_1, REL_2], "rel-1"));
    useUiStore.setState({ selectedRelationshipForRequest: "rel-1" });
    testServer.use(
      http.delete("/v1/miniapp/relationships/:relationshipId", ({ params }) => {
        expect(params.relationshipId).toBe("rel-1");
        state.current = makeBootstrap([REL_2], null);
        return new HttpResponse(null, { status: 204 });
      }),
    );

    renderScreen();
    expect(await screen.findByText("Default")).toBeInTheDocument();
    expect(screen.queryByText("You do not have a default relationship")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Delete: Alex (friend)" }));
    expect(await screen.findByText("Delete this relationship with all its rules?")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    expect(await screen.findByText("You do not have a default relationship")).toBeInTheDocument();
    expect(screen.queryByText("Default")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Set as default: Boss (manager)" })).toBeInTheDocument();
    expect(useUiStore.getState().selectedRelationshipForRequest).toBeNull();
  });

  it("shows not found error when deleting a missing relationship", async () => {
    mockBootstrap(makeBootstrap([REL_1], "rel-1"));
    testServer.use(
      http.delete("/v1/miniapp/relationships/:relationshipId", () =>
        HttpResponse.json({ detail: "Relationship not found" }, { status: 404 }),
      ),
    );

    renderScreen();
    fireEvent.click(await screen.findByRole("button", { name: "Delete: Alex (friend)" }));
    fireEvent.click(await screen.findByRole("button", { name: "Delete" }));

    expect(await screen.findByText("Not found.")).toBeInTheDocument();
  });

  it("sets a relationship as default explicitly", async () => {
    const state = mockBootstrap(makeBootstrap([REL_1, REL_2], null));
    const calls: string[] = [];
    testServer.use(
      http.put("/v1/miniapp/me/default-relationship/:relationshipId", ({ params }) => {
        calls.push(String(params.relationshipId));
        state.current = makeBootstrap([REL_1, REL_2], "rel-2");
        return HttpResponse.json(makeUser({ default_relationship_id: "rel-2" }));
      }),
    );

    renderScreen();
    fireEvent.click(await screen.findByRole("button", { name: "Set as default: Boss (manager)" }));

    await waitFor(() => expect(calls).toEqual(["rel-2"]));
    expect(await screen.findByText("Default")).toBeInTheDocument();
  });

  it("creates a relationship with set_as_default", async () => {
    mockBootstrap(makeBootstrap([REL_1], "rel-1"));
    const bodies: unknown[] = [];
    testServer.use(
      http.post("/v1/miniapp/relationships", async ({ request }) => {
        bodies.push(await request.json());
        return HttpResponse.json(REL_2, { status: 201 });
      }),
    );

    renderScreen();
    fireEvent.change(await screen.findByLabelText("Relation type"), { target: { value: "manager" } });
    fireEvent.change(screen.getByLabelText("Names (comma-separated)"), { target: { value: "Boss" } });
    fireEvent.click(screen.getByLabelText("Make this the default relationship"));
    fireEvent.click(screen.getByRole("button", { name: "Create" }));

    await waitFor(() =>
      expect(bodies).toEqual([
        { relation_type: "manager", aliases: ["Boss"], communication_style: {}, set_as_default: true },
      ]),
    );
  });

  it("navigates to relationship details", async () => {
    mockBootstrap(makeBootstrap([REL_1], "rel-1"));
    renderScreen();
    fireEvent.click(await screen.findByRole("button", { name: "Open: Alex (friend)" }));
    expect(await screen.findByText("details-screen")).toBeInTheDocument();
  });
});
