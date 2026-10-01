import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { loadLanguageOverride } from "../../i18n";
import { useUiStore } from "../../state/uiStore";
import { renderRoutes } from "../../test/render";
import { SettingsScreen } from "./SettingsScreen";

vi.mock("../../telegram", () => ({
  getLaunchLanguage: () => "en",
  getRawInitData: () => "test_init_data",
  initTelegram: () => undefined,
}));

describe("SettingsScreen", () => {
  it("switches UI language and persists the override", async () => {
    renderRoutes({ "/settings": <SettingsScreen /> }, "/settings");

    expect(screen.getByRole("heading", { name: "Settings" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Русский" }));

    expect(await screen.findByRole("heading", { name: "Настройки" })).toBeInTheDocument();
    expect(loadLanguageOverride()).toBe("ru");
    expect(useUiStore.getState().language).toBe("ru");
  });
});
