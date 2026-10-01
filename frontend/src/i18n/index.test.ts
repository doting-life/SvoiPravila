import { describe, expect, it, vi } from "vitest";

vi.mock("../telegram", () => ({
  getLaunchLanguage: () => "en",
}));

import { detectInitialLanguage, getDictionary, loadLanguageOverride, resolveLanguage, saveLanguageOverride } from "./index";
import { en } from "./en";
import { ru } from "./ru";

describe("i18n", () => {
  it("resolves language with ru fallback", () => {
    expect(resolveLanguage("en")).toBe("en");
    expect(resolveLanguage("ru")).toBe("ru");
    expect(resolveLanguage("de")).toBe("ru");
    expect(resolveLanguage(undefined)).toBe("ru");
  });

  it("persists and reads override", () => {
    localStorage.clear();
    expect(loadLanguageOverride()).toBeNull();
    saveLanguageOverride("en");
    expect(loadLanguageOverride()).toBe("en");
  });

  it("prefers local override over telegram language", () => {
    localStorage.clear();
    expect(detectInitialLanguage()).toBe("en");
    saveLanguageOverride("ru");
    expect(detectInitialLanguage()).toBe("ru");
  });

  it("keeps dictionary keys in parity", () => {
    expect(Object.keys(en).sort()).toEqual(Object.keys(ru).sort());
    expect(getDictionary("ru").appTitle).toBe("Свои Правила");
  });
});
