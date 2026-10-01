# Свои Правила Backend v0.4

Deterministic agentic backend for the three MVP workflows:

- `soften` — Смягчить
- `decode` — Расшифровать
- `help-say` — Помоги сказать

The LLM reasons **inside** a stage. Python owns stage order, identity, artifact contracts, retries, checkpoints, provider wiring, authorization, and delivery.

## Mini App frontend (v0.4)

The Telegram Mini App lives in `frontend/` (React + TypeScript + Vite).

```bash
cd frontend
npm install
npm run dev        # proxies /v1 to http://localhost:8000
npm run typecheck && npm run lint && npm test && npm run build
```

`npm run build` writes `frontend/dist`; FastAPI serves it at `/miniapp/` when the directory (`MINIAPP_STATIC_DIR`) exists. `docker compose up --build` builds the frontend and backend into one `app` image. Point the bot's Mini App URL to `https://<host>/miniapp/`.

## Architecture

```text
Telegram Bot / Telegram Mini App / HTTP
                 |
                 v
        Identity + Auth Layer
       Telegram initData -> User
                 |
                 v
       Workflow Engine (Python)
                 |
      +----------+-----------+
      |                      |
      v                      v
 Relationship/User       Stage manifests
 Repositories            + Skills
      |                      |
      v                      v
 PostgreSQL / memory     Typed Artifacts
                             |
                             v
                       Tool Registry
                             |
                    Fake LLM / OpenAI
                             |
                             v
                    Redis checkpoints
```

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
uvicorn app.main:app --reload
```

Defaults use the fake LLM, in-memory repositories, and in-memory checkpoints.

## Production-style infrastructure

```bash
docker compose up -d
```

Example `.env`:

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=<Structured-Outputs-capable model>
RELATIONSHIP_BACKEND=postgres
DATABASE_URL=postgresql+asyncpg://svoi_pravila:svoi_pravila@localhost:5432/svoi_pravila
CHECKPOINT_BACKEND=redis
REDIS_URL=redis://localhost:6379/0

TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=...
TELEGRAM_WEBHOOK_SECRET=<random secret>
TELEGRAM_WEBHOOK_URL=https://your-domain.example/v1/telegram/webhook
TELEGRAM_INIT_DATA_MAX_AGE_SECONDS=3600
```

For a fresh development DB:

```bash
python scripts/init_db.py
```

For an existing v0.2 PostgreSQL DB:

```bash
psql "${DATABASE_URL/postgresql+asyncpg/postgresql}" -f migrations/0002_users_and_miniapp.sql
```

## Telegram Bot

Register the webhook:

```bash
python scripts/set_telegram_webhook.py
```

Inline examples:

```text
soften: Ты опять ничего не сделал
decode: Что он имел в виду?
скажи: Мне не подходит такой вариант
```

Direct messages accept `/soften`, `/decode`, and `/say`.

## Telegram Mini App

The frontend sends the raw `window.Telegram.WebApp.initData` value in:

```http
X-Telegram-Init-Data: <raw initData>
```

The backend validates the Telegram HMAC signature and `auth_date` on every Mini App request. It does **not** trust `initDataUnsafe`, and Mini App request bodies do not contain a trusted `user_id`.

Main Mini App endpoints:

```text
POST   /v1/miniapp/auth
GET    /v1/miniapp/bootstrap
GET    /v1/miniapp/relationships
POST   /v1/miniapp/relationships
PATCH  /v1/miniapp/relationships/{relationship_id}
DELETE /v1/miniapp/relationships/{relationship_id}
PUT    /v1/miniapp/me/default-relationship/{relationship_id}
POST   /v1/miniapp/relationships/{relationship_id}/rules
PUT    /v1/miniapp/relationships/{relationship_id}/rules/{rule_id}
DELETE /v1/miniapp/relationships/{relationship_id}/rules/{rule_id}
POST   /v1/miniapp/assist/{workflow}
```

When `relationship_id` is omitted from an AI request, the workflow loads the user's `default_relationship_id` automatically.

See [docs/MINIAPP_API.md](docs/MINIAPP_API.md).

## Privacy model

- Raw messages are not written to PostgreSQL by the workflow engine.
- Raw prompts/model output are not written to the trace sink.
- Redis checkpoints may temporarily contain request state for retry/resume and expire through TTL.
- Mini App identity is derived only from cryptographically validated Telegram `initData`.
- Relationship access is scoped by internal `user_id`.

## Tests

```bash
pytest -q
```

The suite runs without live OpenAI, PostgreSQL, Redis, or Telegram credentials.
