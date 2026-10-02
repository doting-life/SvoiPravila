import { apiClient } from "./client";

export const miniAppApi = {
  auth: apiClient.auth,
  bootstrap: apiClient.bootstrap,
  listRelationships: apiClient.listRelationships,
  createRelationship: apiClient.createRelationship,
  updateRelationship: apiClient.updateRelationship,
  deleteRelationship: apiClient.deleteRelationship,
  setDefaultRelationship: apiClient.setDefaultRelationship,
  addRule: apiClient.addRule,
  updateRule: apiClient.updateRule,
  deleteRule: apiClient.deleteRule,
  assist: apiClient.assist,
};
