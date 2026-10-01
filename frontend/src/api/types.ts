export type WorkflowName = "soften" | "decode" | "help-say";

export type RelationshipRule = {
  id?: number;
  type: string;
  value: string;
  priority: number;
  created_at?: string;
};

export type UserView = {
  user_id: string;
  telegram_user_id: number;
  first_name: string;
  last_name: string | null;
  username: string | null;
  language_code: string | null;
  default_relationship_id: string | null;
};

export type RelationshipView = {
  relationship_id: string;
  relation_type: string | null;
  aliases: string[];
  communication_style: Record<string, unknown>;
  ruleset_version: number;
  rules: RelationshipRule[];
};

export type AuthResponse = {
  user: UserView;
  auth_date: number;
};

export type BootstrapResponse = {
  user: UserView;
  relationships: RelationshipView[];
};

export type RelationshipCreateBody = {
  relation_type?: string | null;
  aliases?: string[];
  communication_style?: Record<string, unknown>;
  set_as_default?: boolean;
};

export type RelationshipUpdateBody = {
  relation_type?: string | null;
  aliases?: string[];
  communication_style?: Record<string, unknown>;
};

export type RuleBody = {
  type: string;
  value: string;
  priority?: number;
};

export type MiniAppAssistBody = {
  text: string;
  relationship_id?: string | null;
  language?: string | null;
};

export type DeliveryResponse = {
  version: string;
  request_id: string;
  workflow: WorkflowName;
  status: "ok" | "blocked" | "error";
  text: string;
  structured_result: Record<string, unknown> | null;
};
