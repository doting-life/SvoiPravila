import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { AppProviders } from "../app/AppProviders";
import { UiRoot } from "../components/ui";
import { useUiStore } from "../state/uiStore";

export function renderWithUi(ui: ReactElement) {
  return render(<UiRoot>{ui}</UiRoot>);
}

export function resetUiStore(): void {
  useUiStore.setState({
    selectedWorkflow: "soften",
    draftText: "",
    selectedRelationshipForRequest: null,
    language: "ru",
  });
}

export function renderRoutes(routes: Record<string, ReactElement>, initialPath: string) {
  return render(
    <AppProviders>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          {Object.entries(routes).map(([path, element]) => (
            <Route key={path} path={path} element={element} />
          ))}
        </Routes>
      </MemoryRouter>
    </AppProviders>,
  );
}
