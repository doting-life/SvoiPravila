import type { BootstrapResponse, RelationshipView, UserView } from "../api/types";

export function makeUser(overrides: Partial<UserView> = {}): UserView {
  return {
    user_id: "u1",
    telegram_user_id: 1,
    first_name: "A",
    last_name: null,
    username: null,
    language_code: "en",
    default_relationship_id: null,
    ...overrides,
  };
}

export function makeRelationship(overrides: Partial<RelationshipView> = {}): RelationshipView {
  return {
    relationship_id: "rel-1",
    relation_type: "friend",
    aliases: ["Alex"],
    communication_style: {},
    ruleset_version: 0,
    rules: [],
    ...overrides,
  };
}

export function makeBootstrap(
  relationships: RelationshipView[],
  defaultRelationshipId: string | null = null,
): BootstrapResponse {
  return {
    user: makeUser({ default_relationship_id: defaultRelationshipId }),
    relationships,
  };
}
