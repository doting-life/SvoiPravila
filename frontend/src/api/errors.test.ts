import { describe, expect, it, vi } from "vitest";

vi.mock("../telegram", () => ({
  getRawInitData: () => "test_init_data",
}));

import { ApiError } from "./client";
import { toErrorStatus } from "./errors";

describe("toErrorStatus", () => {
  it("maps ApiError to its status", () => {
    expect(toErrorStatus(new ApiError(404, "not found"))).toBe(404);
  });

  it("maps network TypeError to 0", () => {
    expect(toErrorStatus(new TypeError("Failed to fetch"))).toBe(0);
  });

  it("maps unknown errors to 500", () => {
    expect(toErrorStatus(new Error("boom"))).toBe(500);
    expect(toErrorStatus("boom")).toBe(500);
  });
});
