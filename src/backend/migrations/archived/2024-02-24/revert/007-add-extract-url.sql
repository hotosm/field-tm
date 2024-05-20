-- Start a transaction
BEGIN;

-- Update field in projects table
ALTER TABLE IF EXISTS public.projects
DROP COLUMN IF EXISTS data_extract_url;

-- Commit the transaction
COMMIT;
