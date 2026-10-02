// TypeScript usage of @svoi-pravila/miniapp-client.
//
// In a Telegram Mini App, pass `Telegram.WebApp.initData` unchanged:
//
//   const client = createMiniAppClient({
//     initData: () => window.Telegram?.WebApp?.initData,
//     baseUrl: import.meta.env.VITE_API_BASE ?? "",
//   });
//
// The backend derives the user from validated initData; never send user_id.

import {
  createMiniAppClient,
  getStructuredResult,
  isMiniAppApiError,
  type MiniAppClientOptions,
} from "../../clients/typescript/src";

export async function runExample(options: MiniAppClientOptions): Promise<string> {
  const client = createMiniAppClient(options);

  try {
    const { user, relationships } = await client.bootstrap();

    let relationshipId = user.default_relationship_id ?? relationships[0]?.relationship_id ?? null;
    if (!relationshipId) {
      const created = await client.createRelationship({
        relation_type: "spouse",
        aliases: ["Аня"],
        set_as_default: true,
      });
      relationshipId = created.relationship_id;
      await client.addRule(relationshipId, { type: "avoid", value: "не использовать фразу 'ты всегда'", priority: 100 });
    }

    const delivery = await client.assist("soften", {
      text: "Ты всегда откладываешь дела!",
      relationship_id: relationshipId,
      language: "ru",
    });

    const result = getStructuredResult(delivery);
    return result ? result.rewritten_message : delivery.text;
  } catch (err) {
    if (isMiniAppApiError(err)) {
      if (err.isUnauthorized) return "Open the app from Telegram (initData missing or invalid).";
      if (err.isNotConfigured) return "Backend Mini App auth is not configured (TELEGRAM_BOT_TOKEN).";
      return `API error ${err.status}: ${err.detail}`;
    }
    throw err;
  }
}
