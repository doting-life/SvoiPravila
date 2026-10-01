import { ApiError } from "./client";

export function toErrorStatus(err: unknown): number {
  if (err instanceof ApiError) {
    return err.status;
  }
  if (err instanceof TypeError) {
    return 0;
  }
  return 500;
}
