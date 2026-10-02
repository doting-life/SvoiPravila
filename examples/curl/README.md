# curl examples — Mini App API

All `/v1/miniapp/*` endpoints authenticate with the raw Telegram `initData`
string in the `X-Telegram-Init-Data` header. The backend derives the user from
validated initData; never send `user_id`.

```bash
export API=http://localhost:8000
# Real Mini App: the exact Telegram.WebApp.initData string.
# Local development: sign one with the same TELEGRAM_BOT_TOKEN the backend uses:
export INIT_DATA=$(python -c "from examples.python.miniapp_client import sign_init_data; print(sign_init_data('123456:TEST_TOKEN'))")
H="X-Telegram-Init-Data: $INIT_DATA"
```

PowerShell: replace `export X=...` with `$env:X = ...`, use `curl.exe`, and
`$H = "X-Telegram-Init-Data: $env:INIT_DATA"`.

## Session

```bash
curl -s -X POST "$API/v1/miniapp/auth" -H "$H"
curl -s -X GET "$API/v1/miniapp/bootstrap" -H "$H"
```

## Relationships

```bash
curl -s -X GET "$API/v1/miniapp/relationships" -H "$H"

curl -s -X POST "$API/v1/miniapp/relationships" -H "$H" -H "Content-Type: application/json" \
  -d '{"relation_type":"spouse","aliases":["Аня"],"communication_style":{"firmness":"direct"},"set_as_default":true}'

curl -s -X PATCH "$API/v1/miniapp/relationships/rel_7f3c2a9e" -H "$H" -H "Content-Type: application/json" \
  -d '{"aliases":["Аня","Анечка"]}'

curl -s -X PUT "$API/v1/miniapp/me/default-relationship/rel_7f3c2a9e" -H "$H"

curl -s -X DELETE "$API/v1/miniapp/relationships/rel_7f3c2a9e" -H "$H"   # 204
```

## Rules

```bash
curl -s -X POST "$API/v1/miniapp/relationships/rel_7f3c2a9e/rules" -H "$H" -H "Content-Type: application/json" \
  -d '{"type":"avoid","value":"не использовать фразу '\''ты всегда'\''","priority":100}'

curl -s -X PUT "$API/v1/miniapp/relationships/rel_7f3c2a9e/rules/1" -H "$H" -H "Content-Type: application/json" \
  -d '{"type":"avoid","value":"без обобщений","priority":50}'

curl -s -X DELETE "$API/v1/miniapp/relationships/rel_7f3c2a9e/rules/1" -H "$H"   # 204
```

## Assist workflows (`soften`, `decode`, `help-say`)

```bash
curl -s -X POST "$API/v1/miniapp/assist/soften" -H "$H" -H "Content-Type: application/json" \
  -d '{"text":"Ты всегда откладываешь дела!","language":"ru"}'

curl -s -X POST "$API/v1/miniapp/assist/decode" -H "$H" -H "Content-Type: application/json" \
  -d '{"text":"Сейчас не до этого","relationship_id":"rel_7f3c2a9e"}'

curl -s -X POST "$API/v1/miniapp/assist/help-say" -H "$H" -H "Content-Type: application/json" \
  -d '{"text":"Хочу обсудить вчерашний вечер"}'
```

Responses match `docs/openapi.json`; sample payloads live in `docs/fixtures/`.
Errors are `{"detail": "..."}` with 401 (missing/invalid initData),
404 (relationship/rule not owned or missing), 422 (validation; `detail` is a
list), 503 (Mini App auth not configured).
