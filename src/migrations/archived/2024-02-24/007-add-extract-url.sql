-- ## Migration to:
-- * Add public.projects.data_extract_url field.

-- Start a transaction
BEGIN;

-- Update field in projects table
ALTER TABLE IF EXISTS public.projects
ADD COLUMN IF NOT EXISTS data_extract_url VARCHAR;

-- Commit the transaction
COMMIT;
