import { requestJson } from "./client";
import type {
  AuthResponse,
  BootstrapResponse,
  DeliveryResponse,
  MiniAppAssistBody,
  RelationshipCreateBody,
  RelationshipRule,
  RelationshipUpdateBody,
  RelationshipView,
  RuleBody,
  UserView,
  WorkflowName,
} from "./types";

const PREFIX = "/v1/miniapp";

export const miniAppApi = {
  auth: () => requestJson<AuthResponse>(`${PREFIX}/auth`, { method: "POST" }),
  bootstrap: () => requestJson<BootstrapResponse>(`${PREFIX}/bootstrap`),
  listRelationships: () => requestJson<RelationshipView[]>(`${PREFIX}/relationships`),
  createRelationship: (body: RelationshipCreateBody) =>
    requestJson<RelationshipView>(`${PREFIX}/relationships`, { method: "POST", body }),
  updateRelationship: (relationshipId: string, body: RelationshipUpdateBody) =>
    requestJson<RelationshipView>(`${PREFIX}/relationships/${relationshipId}`, {
      method: "PATCH",
      body,
    }),
  deleteRelationship: (relationshipId: string) =>
    requestJson<void>(`${PREFIX}/relationships/${relationshipId}`, { method: "DELETE" }),
  setDefaultRelationship: (relationshipId: string) =>
    requestJson<UserView>(`${PREFIX}/me/default-relationship/${relationshipId}`, { method: "PUT" }),
  addRule: (relationshipId: string, body: RuleBody) =>
    requestJson<RelationshipRule>(`${PREFIX}/relationships/${relationshipId}/rules`, { method: "POST", body }),
  updateRule: (relationshipId: string, ruleId: number, body: RuleBody) =>
    requestJson<RelationshipRule>(`${PREFIX}/relationships/${relationshipId}/rules/${ruleId}`, {
      method: "PUT",
      body,
    }),
  deleteRule: (relationshipId: string, ruleId: number) =>
    requestJson<void>(`${PREFIX}/relationships/${relationshipId}/rules/${ruleId}`, { method: "DELETE" }),
  assist: (workflow: WorkflowName, body: MiniAppAssistBody) =>
    requestJson<DeliveryResponse>(`${PREFIX}/assist/${workflow}`, { method: "POST", body }),
};
