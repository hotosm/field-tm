-- ## Migration to:
-- * Add odk central credentials (str) to organisations table.
-- * Add the approved (bool) field to organisations table.

-- Start a transaction
BEGIN;

ALTER TABLE IF EXISTS public.organisations
    ADD COLUMN IF NOT EXISTS approved BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS odk_central_url VARCHAR,
    ADD COLUMN IF NOT EXISTS odk_central_user VARCHAR,
    ADD COLUMN IF NOT EXISTS odk_central_password VARCHAR;
-- Commit the transaction
COMMIT;
