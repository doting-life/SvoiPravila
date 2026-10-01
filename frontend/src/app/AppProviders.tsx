import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type PropsWithChildren, createContext, useContext, useEffect, useMemo, useState } from "react";

import { UiRoot } from "../components/ui";
import { detectInitialLanguage, getDictionary, saveLanguageOverride, type Language } from "../i18n";
import { useUiStore } from "../state/uiStore";

type LanguageContextValue = {
  language: Language;
  setLanguage: (value: Language) => void;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

function createQueryClient(): QueryClient {
  return new QueryClient({
	defaultOptions: {
	  queries: { retry: false, refetchOnWindowFocus: false },
	  mutations: { retry: false },
	},
  });
}

export function AppProviders({ children, queryClient }: PropsWithChildren<{ queryClient?: QueryClient }>) {
  const [client] = useState<QueryClient>(() => queryClient ?? createQueryClient());
  const [language, setLanguageState] = useState<Language>(detectInitialLanguage);
  const setStoreLanguage = useUiStore((state) => state.setLanguage);

  useEffect(() => {
	setStoreLanguage(language);
  }, [language, setStoreLanguage]);

  const value = useMemo<LanguageContextValue>(
	() => ({
	  language,
	  setLanguage: (nextLanguage) => {
		setLanguageState(nextLanguage);
		saveLanguageOverride(nextLanguage);
	  },
	}),
	[language],
  );

  return (
	<QueryClientProvider client={client}>
	  <LanguageContext.Provider value={value}>
		<UiRoot>{children}</UiRoot>
	  </LanguageContext.Provider>
	</QueryClientProvider>
  );
}

export function useAppLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
	throw new Error("useAppLanguage must be used inside AppProviders");
  }
  return context;
}

export function useT() {
  const { language } = useAppLanguage();
  return getDictionary(language);
}
