CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE OR REPLACE FUNCTION jsonb_values_to_text(jsonb_in JSONB)
RETURNS TEXT LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
    RETURN (SELECT string_agg(value, ' ') FROM jsonb_each_text(jsonb_in));
END;
$$;


CREATE TABLE entries (
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

CREATE INDEX idx_entries_current ON entries (entry_type, is_current) WHERE is_current = TRUE;
CREATE INDEX idx_entries_metadata ON entries USING GIN (metadata);
CREATE INDEX idx_entries_metadata_text_search ON entries USING GIN (jsonb_values_to_text(metadata) gin_trgm_ops);

CREATE TABLE field_registry (
    entry_type  TEXT NOT NULL,
    key         TEXT NOT NULL,
    value_type  TEXT NOT NULL,
    source  TEXT NOT NULL,

    PRIMARY KEY (entry_type, key, source)
);

CREATE INDEX idx_entries_versions ON entries (id, version) WHERE is_current = FALSE;