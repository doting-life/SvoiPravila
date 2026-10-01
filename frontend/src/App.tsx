import { useEffect } from "react";

import { AppProviders, AppRouter } from "./app";
import { initTelegram } from "./telegram";

function AppShell() {
  useEffect(() => {
    initTelegram();
  }, []);

  return <AppRouter />;
}

export function App() {
  return (
    <AppProviders>
      <AppShell />
    </AppProviders>
  );
}
