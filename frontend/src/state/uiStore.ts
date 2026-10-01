import { create } from "zustand";

import type { Language } from "../i18n";
import type { WorkflowName } from "../api/types";

type UiState = {
  selectedWorkflow: WorkflowName;
  draftText: string;
  selectedRelationshipForRequest: string | null;
  language: Language;
  setWorkflow: (workflow: WorkflowName) => void;
  setDraftText: (value: string) => void;
  setRelationshipForRequest: (relationshipId: string | null) => void;
  setLanguage: (language: Language) => void;
};

export const useUiStore = create<UiState>((set) => ({
  selectedWorkflow: "soften",
  draftText: "",
  selectedRelationshipForRequest: null,
  language: "ru",
  setWorkflow: (selectedWorkflow) => set({ selectedWorkflow }),
  setDraftText: (draftText) => set({ draftText }),
  setRelationshipForRequest: (selectedRelationshipForRequest) => set({ selectedRelationshipForRequest }),
  setLanguage: (language) => set({ language }),
}));
