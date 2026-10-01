import { Notice } from "../ui";

export function EmptyState({ message }: { message: string }) {
  return <Notice>{message}</Notice>;
}
