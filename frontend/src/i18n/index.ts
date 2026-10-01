import { en } from "./en";
import { ru, type TranslationDictionary } from "./ru";
import { getLaunchLanguage } from "../telegram";

export type Language = "ru" | "en";
export type { TranslationDictionary };

const LANGUAGE_KEY = "svoi-pravila-language";

const dictionaries: Record<Language, TranslationDictionary> = {
  ru,
  en,
};

export function resolveLanguage(telegramLanguage?: string | null): Language {
  const normalized = telegramLanguage?.toLowerCase();
  if (normalized === "en") {
    return "en";
  }
  return "ru";
}

export function loadLanguageOverride(): Language | null {
  if (typeof localStorage === "undefined") {
    return null;
  }
  const value = localStorage.getItem(LANGUAGE_KEY);
  return value === "en" || value === "ru" ? value : null;
}

export function saveLanguageOverride(language: Language): void {
  if (typeof localStorage === "undefined") {
    return;
  }
  localStorage.setItem(LANGUAGE_KEY, language);
}

export function detectInitialLanguage(): Language {
  return loadLanguageOverride() ?? resolveLanguage(getLaunchLanguage());
}

export function getDictionary(language: Language): TranslationDictionary {
  return dictionaries[language];
}

export function t(language: Language, key: keyof TranslationDictionary): string {
  return dictionaries[language][key];
}
