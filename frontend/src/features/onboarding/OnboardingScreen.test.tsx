import { fireEvent, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import { testServer } from "../../test/setup";
import { makeBootstrap, makeRelationship } from "../../test/fixtures";
import { renderRoutes } from "../../test/render";
import { OnboardingScreen } from "./OnboardingScreen";

vi.mock("../../telegram", () => ({
  getLaunchLanguage: () => "en",
  getRawInitData: () => "test_init_data",
  initTelegram: () => undefined,
}));

function renderOnboarding() {
  return renderRoutes(
    {
      "/onboarding": <OnboardingScreen />,
      "/": <div>main-screen</div>,
    },
    "/onboarding",
  );
}

describe("OnboardingScreen", () => {
  it("creates the first relationship and optional rule", async () => {
    const bodies: unknown[] = [];
    testServer.use(
      http.post("/v1/miniapp/relationships", async ({ request }) => {
        bodies.push(await request.json());
        return HttpResponse.json(makeRelationship(), { status: 201 });
      }),
      http.post("/v1/miniapp/relationships/:relationshipId/rules", async ({ request }) => {
        bodies.push(await request.json());
        return HttpResponse.json({ id: 1, type: "tone", value: "calm", priority: 0 }, { status: 201 });
      }),
      http.get("/v1/miniapp/bootstrap", () => HttpResponse.json(makeBootstrap([makeRelationship()], "rel-1"))),
    );

    renderOnboarding();

    fireEvent.change(screen.getByLabelText("Relation type"), { target: { value: "friend" } });
    fireEvent.change(screen.getByLabelText("Names (comma-separated)"), { target: { value: "Alex, Sasha" } });
    fireEvent.change(screen.getByLabelText("Rule type"), { target: { value: "tone" } });
    fireEvent.change(screen.getByLabelText("Rule text"), { target: { value: "calm" } });
    fireEvent.click(screen.getByRole("button", { name: "Create" }));

    await waitFor(() => expect(screen.getByText("main-screen")).toBeInTheDocument());
    expect(bodies).toEqual([
      { relation_type: "friend", aliases: ["Alex", "Sasha"], communication_style: {}, set_as_default: true },
      { type: "tone", value: "calm", priority: 0 },
    ]);
  });

  it("maps backend error status to a localized message", async () => {
    testServer.use(
      http.post("/v1/miniapp/relationships", () =>
        HttpResponse.json({ detail: "Telegram Mini App authentication is not configured" }, { status: 503 }),
      ),
    );

    renderOnboarding();
    fireEvent.click(screen.getByRole("button", { name: "Create" }));

    expect(await screen.findByText("Mini App service is not configured.")).toBeInTheDocument();
  });

  it("maps network failures to the network error message", async () => {
    testServer.use(http.post("/v1/miniapp/relationships", () => HttpResponse.error()));

    renderOnboarding();
    fireEvent.click(screen.getByRole("button", { name: "Create" }));

    expect(await screen.findByText("Network error")).toBeInTheDocument();
  });
});
