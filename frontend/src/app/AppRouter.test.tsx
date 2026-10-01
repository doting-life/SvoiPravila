import { fireEvent, render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { makeBootstrap, makeRelationship } from "../test/fixtures";
import { resetUiStore } from "../test/render";
import { testServer } from "../test/setup";
import { useUiStore } from "../state/uiStore";
import { AppProviders } from "./AppProviders";
import { AppRoutes } from "./AppRouter";

vi.mock("../telegram", () => ({
  getLaunchLanguage: () => "en",
  getRawInitData: () => "test_init_data",
  initTelegram: () => undefined,
  attachBackButton: () => () => undefined,
  copyText: async () => true,
}));

function renderApp(path = "/") {
  return render(
    <AppProviders>
      <MemoryRouter initialEntries={[path]}>
        <AppRoutes />
      </MemoryRouter>
    </AppProviders>,
  );
}

describe("BootstrapGate", () => {
  beforeEach(() => {
    resetUiStore();
  });

  it("redirects to onboarding when the user has no relationships", async () => {
    testServer.use(http.get("/v1/miniapp/bootstrap", () => HttpResponse.json(makeBootstrap([], null))));
    renderApp("/");
    expect(await screen.findByText("Create your first relationship")).toBeInTheDocument();
  });

  it("renders the main screen with navigation when relationships exist", async () => {
    testServer.use(
      http.get("/v1/miniapp/bootstrap", () => HttpResponse.json(makeBootstrap([makeRelationship()], "rel-1"))),
    );
    renderApp("/");
    expect(await screen.findByRole("button", { name: "Submit" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Settings" }));
    expect(await screen.findByRole("heading", { name: "Settings", level: 1 })).toBeInTheDocument();
  });

  it("shows a localized error with retry", async () => {
    let calls = 0;
    testServer.use(
      http.get("/v1/miniapp/bootstrap", () => {
        calls += 1;
        if (calls === 1) {
          return HttpResponse.json({ detail: "expired" }, { status: 401 });
        }
        return HttpResponse.json(makeBootstrap([makeRelationship()], "rel-1"));
      }),
    );
    renderApp("/");
    expect(await screen.findByText("Session expired. Reopen the Mini App from Telegram.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByRole("button", { name: "Submit" })).toBeInTheDocument();
  });

  it("syncs the store language with the detected language", async () => {
    testServer.use(http.get("/v1/miniapp/bootstrap", () => HttpResponse.json(makeBootstrap([], null))));
    renderApp("/");
    await screen.findByText("Create your first relationship");
    expect(useUiStore.getState().language).toBe("en");
  });
});
