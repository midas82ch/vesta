CREATE TYPE offer_availability AS ENUM (
    'confirmed',
    'call_to_confirm',
    'unknown'
);

CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    contact_email TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE offers (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    summary TEXT NOT NULL,
    languages TEXT[] NOT NULL DEFAULT '{}',
    location GEOGRAPHY(POINT, 4326),
    access_rules JSONB NOT NULL DEFAULT '{}',
    contact JSONB NOT NULL DEFAULT '{}',
    availability offer_availability NOT NULL DEFAULT 'unknown',
    published BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE offer_categories (
    offer_id UUID NOT NULL REFERENCES offers(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    PRIMARY KEY (offer_id, category)
);

CREATE TABLE offer_verifications (
    id UUID PRIMARY KEY,
    offer_id UUID NOT NULL REFERENCES offers(id) ON DELETE CASCADE,
    source_label TEXT NOT NULL,
    source_url TEXT,
    verified_by TEXT NOT NULL,
    verified_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE knowledge_chunks (
    id UUID PRIMARY KEY,
    offer_id UUID REFERENCES offers(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    source_url TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    embedding VECTOR(1536)
);

CREATE TABLE anonymous_outcomes (
    id UUID PRIMARY KEY,
    need TEXT NOT NULL,
    result TEXT NOT NULL,
    barrier TEXT,
    offer_id UUID REFERENCES offers(id) ON DELETE SET NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX offers_location_idx ON offers USING GIST (location);
CREATE INDEX knowledge_chunks_embedding_idx
    ON knowledge_chunks
    USING hnsw (embedding vector_cosine_ops);
