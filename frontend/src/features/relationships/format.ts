import type { RelationshipView } from "../../api/types";
import type { TranslationDictionary } from "../../i18n";

export const RELATION_TYPE_MAX_LENGTH = 64;
export const MAX_ALIASES = 20;

export function relationshipLabel(relationship: RelationshipView, dict: TranslationDictionary): string {
  const alias = relationship.aliases.find((value) => value.trim().length > 0);
  const type = relationship.relation_type?.trim();
  if (alias && type) {
    return `${alias} (${type})`;
  }
  return alias ?? type ?? dict.relationshipUnnamed;
}

export function parseAliases(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0)
    .slice(0, MAX_ALIASES);
}
