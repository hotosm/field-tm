BEGIN;

CREATE TABLE IF NOT EXISTS project_external_urls (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    url TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (project_id, source)
);

CREATE INDEX IF NOT EXISTS project_external_urls_project_source_idx
ON project_external_urls (project_id, source);

COMMIT;
