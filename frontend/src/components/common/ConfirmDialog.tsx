import { t, type Language } from "../../i18n";
import { Button, Modal, Row, Stack } from "../ui";

export function ConfirmDialog({
  language,
  message,
  onConfirm,
  onCancel,
}: {
  language: Language;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <Modal open onClose={onCancel}>
      <Stack>
        <p>{message}</p>
        <Row>
          <Button mode="filled" onClick={onConfirm}>
            {t(language, "delete")}
          </Button>
          <Button mode="bezeled" onClick={onCancel}>
            {t(language, "cancel")}
          </Button>
        </Row>
      </Stack>
    </Modal>
  );
}
