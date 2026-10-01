import { t, type Language } from "../../i18n";
import { Spinner } from "../ui";

export function LoadingState({ language }: { language: Language }) {
  return <Spinner label={t(language, "loading")} />;
}
