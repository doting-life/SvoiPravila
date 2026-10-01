import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { renderWithUi } from "../../test/render";
import { ErrorState } from "./ErrorState";

describe("ErrorState", () => {
  it("renders auth error text for 401", () => {
    renderWithUi(<ErrorState language="ru" status={401} />);
    expect(screen.getByText(/Сессия истекла/i)).toBeInTheDocument();
  });

  it("renders service unavailable text for 503", () => {
    renderWithUi(<ErrorState language="en" status={503} />);
    expect(screen.getByText(/not configured/i)).toBeInTheDocument();
  });

  it("renders not found text for 404", () => {
    renderWithUi(<ErrorState language="en" status={404} />);
    expect(screen.getByText("Not found.")).toBeInTheDocument();
  });

  it("renders network text for synthetic status 0", () => {
    renderWithUi(<ErrorState language="en" status={0} />);
    expect(screen.getByText("Network error")).toBeInTheDocument();
  });

  it("calls retry handler", () => {
    const onRetry = vi.fn();
    renderWithUi(<ErrorState language="en" status={500} onRetry={onRetry} />);
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });
});
