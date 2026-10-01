# Telegram Mini App API — v0.3

## Authentication contract

The Mini App sends the **raw** value of `window.Telegram.WebApp.initData` in every API request:

```http
X-Telegram-Init-Data: <raw Telegram.WebApp.initData query string>
```

The backend does not trust `initDataUnsafe` and does not accept a client-supplied `user_id` for Mini App operations. It verifies Telegram's HMAC-SHA-256 signature and checks `auth_date` against `TELEGRAM_INIT_DATA_MAX_AGE_SECONDS`.

After validation, `telegram_user_id` is mapped to an internal `user_id`. The first valid request creates the user; later requests update non-sensitive Telegram profile fields such as display name, username, and language code.

This v0.3 implementation intentionally remains stateless at the HTTP auth layer: it validates `initData` on each Mini App request instead of minting a second application session token. That keeps identity derivation simple and avoids another credential/session store during MVP.

## Bootstrap

`GET /v1/miniapp/bootstrap`

Returns the authenticated user plus all owned relationships and rules. It is intended as the initial Mini App load endpoint.

## Relationships

- `GET /v1/miniapp/relationships`
- `POST /v1/miniapp/relationships`
- `PATCH /v1/miniapp/relationships/{relationship_id}`
- `DELETE /v1/miniapp/relationships/{relationship_id}`
- `PUT /v1/miniapp/me/default-relationship/{relationship_id}`

The first created relationship automatically becomes the default unless another default already exists. A caller can also set `set_as_default: true` when creating a relationship.

A relationship can only be read, changed, selected, or used by its owner.

## Rules

- `POST /v1/miniapp/relationships/{relationship_id}/rules`
- `PUT /v1/miniapp/relationships/{relationship_id}/rules/{rule_id}`
- `DELETE /v1/miniapp/relationships/{relationship_id}/rules/{rule_id}`

Every rule mutation increments `ruleset_version`. The workflow receives the current rules through `RelationshipContext`.

## AI requests

`POST /v1/miniapp/assist/{workflow}` where workflow is one of:

- `soften`
- `decode`
- `help-say`

Request body:

```json
{
  "text": "Ты опять всё отложил",
  "relationship_id": null,
  "language": "ru"
}
```

`relationship_id` is optional. When omitted, `ContextStage` resolves the authenticated user's `default_relationship_id`. The client cannot choose another user's relationship: ownership is checked before workflow execution.

## Database migration

Fresh development databases can still use:

```bash
python scripts/init_db.py
```

Existing v0.2 PostgreSQL installations should additionally apply:

```bash
psql "${DATABASE_URL/postgresql+asyncpg/postgresql}" -f migrations/0002_users_and_miniapp.sql
```

The migration adds the `users` table and a `NOT VALID` relationship foreign key so legacy rows are not destroyed. Legacy application users should be mapped explicitly before validating the constraint.

## Frontend hosting (v0.4)

The built Mini App is served by FastAPI at `/miniapp/` when `MINIAPP_STATIC_DIR` (default `frontend/dist`) exists; otherwise `/miniapp` returns 404. The frontend calls only `/v1/miniapp/*` and sends raw `Telegram.WebApp.initData` in `X-Telegram-Init-Data` on every request. `/v1/assist/*` remains internal and is not used by the frontend.

