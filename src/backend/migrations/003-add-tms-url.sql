-- ## Migration to:
-- * Add field projects.tms_url (str).

-- Start a transaction
BEGIN;

ALTER TABLE IF EXISTS public.projects
ADD COLUMN IF NOT EXISTS custom_tms_url VARCHAR;
-- Commit the transaction
COMMIT;
