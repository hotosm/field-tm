-- Start a transaction
BEGIN;

ALTER TABLE IF EXISTS public.projects
DROP COLUMN IF EXISTS custom_tms_url;
-- Commit the transaction
COMMIT;
