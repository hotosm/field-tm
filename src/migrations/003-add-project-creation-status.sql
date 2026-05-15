-- Track asynchronous project-creation pipeline state.
-- The simple-flow create endpoint enqueues the heavy finalize work as a
-- background task; the frontend polls creation_status to know when to
-- redirect into the project view.
ALTER TABLE IF EXISTS projects
ADD COLUMN IF NOT EXISTS creation_status character varying DEFAULT 'ready',
ADD COLUMN IF NOT EXISTS creation_error text,
ADD COLUMN IF NOT EXISTS creation_updated_at timestamp with time zone;

UPDATE projects
SET creation_status = 'ready'
WHERE creation_status IS NULL;
