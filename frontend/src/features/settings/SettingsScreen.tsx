import { type Language } from "../../i18n";
import { useAppLanguage, useT } from "../../app/AppProviders";
import { Button, Card, Row, Stack } from "../../components/ui";

export function SettingsScreen() {
  const dict = useT();
  const { language, setLanguage } = useAppLanguage();
  const options: { value: Language; label: string }[] = [
    { value: "ru", label: dict.languageRu },
    { value: "en", label: dict.languageEn },
  ];

  return (
    <Stack>
      <h1>{dict.settings}</h1>
      <Card header={dict.language}>
        <Stack>
          <Row>
            {options.map((option) => (
              <Button
                key={option.value}
                mode={option.value === language ? "filled" : "bezeled"}
                aria-pressed={option.value === language}
                onClick={() => setLanguage(option.value)}
              >
                {option.label}
              </Button>
            ))}
          </Row>
        </Stack>
      </Card>
    </Stack>
  );
}
