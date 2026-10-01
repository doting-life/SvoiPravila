import * as telegramSdk from "@tma.js/sdk-react";

export type TelegramWebApp = {
  ready?: () => void;
  expand?: () => void;
  initData?: string;
  initDataUnsafe?: { user?: { language_code?: string } };
  BackButton?: {
    show: () => void;
    hide: () => void;
    onClick: (callback: () => void) => void;
    offClick: (callback: () => void) => void;
  };
  HapticFeedback?: {
    impactOccurred?: (style: "light" | "medium" | "heavy" | "rigid" | "soft") => void;
  };
};

type SdkInit = {
  init?: () => void;
};

const sdk = telegramSdk as SdkInit;

function getTelegramWebApp(): TelegramWebApp | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.Telegram?.WebApp ?? null;
}

export function initTelegram(): void {
  sdk.init?.();
  const webApp = getTelegramWebApp();
  webApp?.ready?.();
  webApp?.expand?.();
}

export function getRawInitData(): string | null {
  const webApp = getTelegramWebApp();
  if (webApp?.initData) {
    return webApp.initData;
  }
  return resolveDevInitData(import.meta.env.DEV, import.meta.env.VITE_DEV_INIT_DATA);
}

export function resolveDevInitData(isDev: boolean, fallbackValue: string | undefined): string | null {
  if (!isDev) {
    return null;
  }
  return fallbackValue ? fallbackValue : null;
}

export function getLaunchLanguage(): string {
  const lang = getTelegramWebApp()?.initDataUnsafe?.user?.language_code?.toLowerCase();
  return lang ?? "ru";
}

export function attachBackButton(handler: () => void): () => void {
  const webApp = getTelegramWebApp();
  const button = webApp?.BackButton;
  if (!button) {
    return () => undefined;
  }
  button.show();
  button.onClick(handler);
  return () => {
    button.offClick(handler);
    button.hide();
  };
}

export const useBackButton = attachBackButton;

export function haptic(
  getTelegramWebApp()?.HapticFeedback?.impactOccurred?.(style);
}

export async function copyText(value: string): Promise<boolean> {
  if (typeof navigator === "undefined" || !navigator.clipboard) {
    return false;
  }
  await navigator.clipboard.writeText(value);
  return true;
}
