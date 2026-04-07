-- Temporary job state shared between the backend and qfield-qgis containers
-- for QGIS project generation.  Rows are short-lived (seconds to minutes) and
-- deleted by the backend after processing.  A periodic cleanup removes orphans
-- from crashed jobs.

CREATE TABLE IF NOT EXISTS qgis_jobs (
    job_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Inputs (written by backend, read by QGIS wrapper)
    xlsform BYTEA,
    features JSONB,
    tasks JSONB,
    -- Outputs (written by QGIS wrapper, read by backend)
    -- Dict of {filename: base64_content_string}
    output_files JSONB
);
ALTER TABLE qgis_jobs OWNER TO current_user;

-- Clean up orphaned jobs older than 1 hour (crash recovery).
-- Run via application startup or periodic task; kept here for reference.
-- DELETE FROM qgis_jobs WHERE created_at < NOW() - INTERVAL '1 hour';
