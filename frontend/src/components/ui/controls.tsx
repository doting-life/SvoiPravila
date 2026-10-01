import {
  Button as TgButton,
  Checkbox as TgCheckbox,
  Cell as TgCell,
  Input as TgInput,
  Select as TgSelect,
  Textarea as TgTextarea,
} from "@telegram-apps/telegram-ui";
import type { ComponentProps, ReactNode } from "react";

type TgButtonProps = ComponentProps<typeof TgButton>;

export function Button({ type = "button", size = "m", ...props }: TgButtonProps) {
  return <TgButton type={type} size={size} {...props} />;
}

type LabeledProps = {
  label: string;
  error?: string | null;
};

export function Input({ label, error, ...props }: Omit<ComponentProps<typeof TgInput>, "header" | "status"> & LabeledProps) {
  return <TgInput header={label} aria-label={label} status={error ? "error" : "default"} {...props} />;
}

export function TextArea({
  label,
  error,
  ...props
}: Omit<ComponentProps<typeof TgTextarea>, "header" | "status"> & LabeledProps) {
  return <TgTextarea header={label} aria-label={label} status={error ? "error" : "default"} {...props} />;
}

export function Select({
  label,
  children,
  ...props
}: Omit<ComponentProps<typeof TgSelect>, "header" | "children"> & { label: string; children: ReactNode }) {
  return (
    <TgSelect header={label} aria-label={label} {...props}>
      {children}
    </TgSelect>
  );
}

export function Checkbox({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <TgCell
      Component="label"
      before={<TgCheckbox aria-label={label} checked={checked} onChange={(event) => onChange(event.target.checked)} />}
      multiline
    >
      {label}
    </TgCell>
  );
}
