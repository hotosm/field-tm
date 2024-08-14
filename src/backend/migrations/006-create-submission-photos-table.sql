-- ## Migration to:
-- * Create submission_photos table

-- Start a transaction
BEGIN;

CREATE TABLE IF NOT EXISTS submission_photos (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    submission_id VARCHAR NOT NULL,
    s3_path VARCHAR NOT NULL
);
ALTER TABLE public.submission_photos OWNER TO fmtm;

-- Commit the transaction
COMMIT;
