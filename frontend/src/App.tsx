import { useEffect } from "react";

import { AppProviders, AppRouter } from "./app/index";
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
