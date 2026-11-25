CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE OR REPLACE FUNCTION jsonb_values_to_text(jsonb_in JSONB)
RETURNS TEXT LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
    RETURN (SELECT string_agg(value, ' ') FROM jsonb_each_text(jsonb_in));
END;
$$;


CREATE TABLE IF NOT EXISTS entries (
    id               UUID DEFAULT gen_random_uuid(),
    version          INTEGER NOT NULL DEFAULT 1,
    is_current       BOOLEAN NOT NULL DEFAULT TRUE,
    entry_type       TEXT NOT NULL,
    source           TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by       TEXT NOT NULL,
    metadata         JSONB NOT NULL DEFAULT '{}',
    metadata_sources JSONB NOT NULL DEFAULT '{}',

    PRIMARY KEY (id, version)
);

CREATE INDEX IF NOT EXISTS idx_entries_current ON entries (entry_type, is_current) WHERE is_current = TRUE;
CREATE INDEX IF NOT EXISTS idx_entries_metadata ON entries USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_entries_metadata_text_search ON entries USING GIN (jsonb_values_to_text(metadata) gin_trgm_ops);

CREATE TABLE IF NOT EXISTS field_registry (
    entry_type  TEXT NOT NULL,
    key         TEXT NOT NULL,
    value_type  TEXT NOT NULL,
    source      TEXT NOT NULL,

    PRIMARY KEY (entry_type, key, source)
);

CREATE INDEX IF NOT EXISTS idx_entries_versions ON entries (id, version) WHERE is_current = FALSE;

CREATE TABLE IF NOT EXISTS collections (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    owner       TEXT NOT NULL,
    is_public   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_collections_owner ON collections (owner);

CREATE TABLE IF NOT EXISTS collection_memberships (
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    entry_id      UUID NOT NULL,
    added_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    added_by      TEXT NOT NULL,

    PRIMARY KEY (collection_id, entry_id)
);

CREATE TABLE IF NOT EXISTS jobs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type   TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',
    owner       TEXT NOT NULL,
    payload     JSONB NOT NULL DEFAULT '{}',
    result      JSONB,
    error       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_owner_status ON jobs (owner, status);
