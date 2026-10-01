-- v0.3: Telegram Mini App identity and user/default-relationship support.
-- Designed for PostgreSQL. Run after v0.2 schema creation on existing installations.

CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(64) PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL UNIQUE,
    first_name VARCHAR(256) NOT NULL,
    last_name VARCHAR(256),
    username VARCHAR(64),
    language_code VARCHAR(16),
    default_relationship_id VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_users_telegram_user_id ON users (telegram_user_id);

-- Existing v0.2 relationship rows may refer to legacy application user ids for
-- which no users row exists. NOT VALID preserves those historical rows while
-- enforcing the foreign key for new/changed rows. Validate after legacy users
-- have been explicitly mapped to Telegram identities.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_relationships_user_id_users'
    ) THEN
        ALTER TABLE relationships
            ADD CONSTRAINT fk_relationships_user_id_users
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            NOT VALID;
    END IF;
END $$;
