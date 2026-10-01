# Security and Privacy

## Data minimization

По умолчанию продукт не хранит полный текст пользовательских сообщений после завершения запроса.

## Persistent data

Разрешено хранить:
- relationship configuration;
- user-authored rules;
- preferences;
- ruleset history;
- technical telemetry;
- explicit user feedback.

## Ephemeral data

Raw message content и intermediate artifacts могут храниться только на время выполнения запроса и должны иметь TTL.

## Secrets

- API keys только через secret manager/environment;
- никогда не передавать keys в skill context;
- redact secrets from logs;
- provider errors sanitise before persistent logging.

## Access boundaries

Mini App / Telegram clients не должны получать внутренние prompts, hidden rules, provider credentials или internal validation traces.

## Provider boundary

Manifest каждого tool должен явно указывать, отправляет ли он raw user text третьему provider.
