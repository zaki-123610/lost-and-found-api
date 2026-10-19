-- Database schema. Safe to run on every startup: existing tables are left untouched.

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email         TEXT        NOT NULL UNIQUE,
    password_hash TEXT        NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS items (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     INTEGER     NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    type        TEXT        NOT NULL CHECK (type IN ('lost', 'found')),
    title       TEXT        NOT NULL,
    description TEXT,
    category    TEXT        NOT NULL,
    location    TEXT        NOT NULL,
    event_date  DATE        NOT NULL,
    status      TEXT        NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'recovered')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS items_user_id_idx ON items (user_id);
CREATE INDEX IF NOT EXISTS items_created_at_idx ON items (created_at);
