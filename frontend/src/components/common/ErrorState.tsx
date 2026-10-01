import { t, type Language } from "../../i18n";
import { Button, Notice, Stack } from "../ui";

function resolveMessage(language: Language, status?: number): string {
  if (status === 401) {
    return t(language, "errorUnauthorized");
  }
  if (status === 503) {
    return t(language, "errorServiceUnavailable");
  }
  if (status === 404) {
    return t(language, "errorNotFound");
  }
  if (status === 0) {
    return t(language, "errorNetwork");
  }
  return t(language, "errorGeneric");
}

export function ErrorState({
  language,
  status,
  onRetry,
}: {
  language: Language;
  status?: number;
  onRetry?: () => void;
}) {
  return (
    <Stack>
      <Notice tone="error">{resolveMessage(language, status)}</Notice>
      {onRetry ? <Button onClick={onRetry}>{t(language, "retry")}</Button> : null}
    </Stack>
  );
}
