import { describe, expect, it } from "vitest";

import { useUiStore } from "./uiStore";

describe("ui store", () => {
  it("updates workflow and in-memory draft state", () => {
    useUiStore.setState({
      selectedWorkflow: "soften",
      draftText: "",
      selectedRelationshipForRequest: null,
      language: "ru",
    });

    useUiStore.getState().setWorkflow("decode");
    useUiStore.getState().setDraftText("hello");
    useUiStore.getState().setRelationshipForRequest("rel-1");

    const state = useUiStore.getState();
    expect(state.selectedWorkflow).toBe("decode");
    expect(state.draftText).toBe("hello");
    expect(state.selectedRelationshipForRequest).toBe("rel-1");
  });
});
