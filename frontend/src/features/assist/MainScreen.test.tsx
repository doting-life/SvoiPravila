import { fireEvent, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { DeliveryResponse, RelationshipView, WorkflowName } from "../../api/types";
import { makeBootstrap, makeRelationship } from "../../test/fixtures";
import { renderRoutes, resetUiStore } from "../../test/render";
import { testServer } from "../../test/setup";
import { MainScreen } from "./MainScreen";

vi.mock("../../telegram", () => ({
  getLaunchLanguage: () => "en",
  getRawInitData: () => "test_init_data",
  initTelegram: () => undefined,
  attachBackButton: () => () => undefined,
  copyText: vi.fn(async () => true),
}));

const REL_1 = makeRelationship({ relationship_id: "rel-1", aliases: ["Alex"], relation_type: "friend" });
const REL_2 = makeRelationship({ relationship_id: "rel-2", aliases: ["Boss"], relation_type: "manager" });

function delivery(workflow: WorkflowName, overrides: Partial<DeliveryResponse> = {}): DeliveryResponse {
  const structured: Record<WorkflowName, Record<string, unknown>> = {
    soften: {
      version: "1.0",
      request_id: "11111111-1111-1111-1111-111111111111",
      original_intent: "ask to stop",
      rewritten_message: "Could you please stop?",
      tone_applied: "gentle",
      constraints_respected: ["no blame"],
    },
    decode: {
      version: "1.0",
      request_id: "11111111-1111-1111-1111-111111111111",
      literal_meaning: "Fine.",
      probable_intent: "Upset",
      emotional_tone: "cold",
      uncertainty: "medium",
      alternative_interpretations: ["Tired"],
    },
    "help-say": {
      version: "1.0",
      request_id: "11111111-1111-1111-1111-111111111111",
      message: "I need some time.",
      tone: "calm",
      preserved_intent: "ask for space",
      warnings: [],
    },
  };
  return {
    version: "1.0",
    request_id: "11111111-1111-1111-1111-111111111111",
    workflow,
    status: "ok",
    text: "plain text",
    structured_result: structured[workflow],
    ...overrides,
  };
}

function setup(relationships: RelationshipView[], defaultId: string | null, response?: DeliveryResponse) {
  const bodies: Record<string, unknown>[] = [];
  const workflows: string[] = [];
  testServer.use(
    http.get("/v1/miniapp/bootstrap", () => HttpResponse.json(makeBootstrap(relationships, defaultId))),
    http.post("/v1/miniapp/assist/:workflow", async ({ params, request }) => {
      const workflow = String(params.workflow) as WorkflowName;
      workflows.push(workflow);
      bodies.push((await request.json()) as Record<string, unknown>);
      return HttpResponse.json(response ?? delivery(workflow));
    }),
  );
  renderRoutes({ "/": <MainScreen /> }, "/");
  return { bodies, workflows };
}

async function typeAndSubmit(value: string) {
  fireEvent.change(await screen.findByLabelText("Enter text"), { target: { value } });
  fireEvent.click(screen.getByRole("button", { name: "Submit" }));
}

describe("MainScreen", () => {
  beforeEach(() => {
    resetUiStore();
  });

  it("uses the default relationship without sending relationship_id (soften)", async () => {
    const { bodies } = setup([REL_1, REL_2], "rel-1");
    expect(await screen.findByText("Default relationship is used: Alex (friend)")).toBeInTheDocument();

    await typeAndSubmit("stop it");

    expect(await screen.findByText("Could you please stop?")).toBeInTheDocument();
    expect(screen.getByText("Softened message")).toBeInTheDocument();
    expect(bodies).toEqual([{ text: "stop it", language: "en" }]);
  });

  it("renders the decode result", async () => {
    const { workflows } = setup([REL_1], "rel-1");
    fireEvent.click(await screen.findByRole("button", { name: "Decode" }));
    await typeAndSubmit("Fine.");

    expect(await screen.findByText("Upset")).toBeInTheDocument();
    expect(screen.getByText("Literal meaning")).toBeInTheDocument();
    expect(workflows).toEqual(["decode"]);
  });

  it("renders the help-say result", async () => {
    const { workflows } = setup([REL_1], "rel-1");
    fireEvent.click(await screen.findByRole("button", { name: "Help Say" }));
    await typeAndSubmit("I need space");

    expect(await screen.findByText("I need some time.")).toBeInTheDocument();
    expect(workflows).toEqual(["help-say"]);
  });

  it("falls back to text when structured_result is missing", async () => {
    setup([REL_1], "rel-1", delivery("soften", { structured_result: null, text: "fallback text" }));
    await typeAndSubmit("hello");
    expect(await screen.findByText("fallback text")).toBeInTheDocument();
  });

  it("sends relationship_id for a one-off override", async () => {
    const { bodies } = setup([REL_1, REL_2], "rel-1");
    fireEvent.change(await screen.findByLabelText("Choose a relationship for this request"), {
      target: { value: "rel-2" },
    });
    expect(screen.queryByText(/Default relationship is used/)).not.toBeInTheDocument();

    await typeAndSubmit("hello");
    await screen.findByText("Could you please stop?");
    expect(bodies).toEqual([{ text: "hello", language: "en", relationship_id: "rel-2" }]);
  });

  it("does not preselect anything without a default and sends the selected id", async () => {
    const { bodies } = setup([REL_1, REL_2], null);
    expect(await screen.findByText("You do not have a default relationship")).toBeInTheDocument();
    const select = screen.getByLabelText("Choose a relationship for this request") as HTMLSelectElement;
    expect(select.value).toBe("");

    fireEvent.change(select, { target: { value: "rel-1" } });
    expect(screen.queryByText("The request will be sent without relationship context")).not.toBeInTheDocument();

    await typeAndSubmit("hello");
    await screen.findByText("Could you please stop?");
    expect(bodies).toEqual([{ text: "hello", language: "en", relationship_id: "rel-1" }]);
  });

  it("sends without relationship_id and shows a notice when nothing is selected", async () => {
    const { bodies } = setup([REL_1], null);
    expect(await screen.findByText("The request will be sent without relationship context")).toBeInTheDocument();

    await typeAndSubmit("hello");
    await screen.findByText("Could you please stop?");
    expect(bodies).toEqual([{ text: "hello", language: "en" }]);
  });

  it("shows the blocked view", async () => {
    setup([REL_1], "rel-1", delivery("soften", { status: "blocked", text: "Cannot help", structured_result: null }));
    await typeAndSubmit("hello");
    expect(await screen.findByText("Request was blocked")).toBeInTheDocument();
    expect(screen.getByText("Cannot help")).toBeInTheDocument();
  });

  it("shows an error view on backend failure", async () => {
    testServer.use(
      http.get("/v1/miniapp/bootstrap", () => HttpResponse.json(makeBootstrap([REL_1], "rel-1"))),
      http.post("/v1/miniapp/assist/:workflow", () => HttpResponse.json({ detail: "boom" }, { status: 500 })),
    );
    renderRoutes({ "/": <MainScreen /> }, "/");
    await typeAndSubmit("hello");
    expect(await screen.findByText("Something went wrong.")).toBeInTheDocument();
  });

  it("validates empty and too long input without calling the API", async () => {
    const { bodies } = setup([REL_1], "rel-1");
    await typeAndSubmit("   ");
    expect(await screen.findAllByText("Enter some text")).not.toHaveLength(0);

    await typeAndSubmit("a".repeat(10_001));
    expect(await screen.findAllByText("Text must not exceed 10,000 characters")).not.toHaveLength(0);

    await waitFor(() => expect(bodies).toHaveLength(0));
  });
});
