BEGIN;

-- Add qfield_project_id to project_external_urls

ALTER TABLE ONLY public.project_external_urls
ADD COLUMN IF NOT EXISTS qfield_project_id VARCHAR;

COMMIT;
