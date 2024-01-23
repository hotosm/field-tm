-- Start a transaction
BEGIN;

-- Remove the odk central credentials columns and approved column
--- from the public.organisations table
ALTER TABLE IF EXISTS public.organisations
    DROP COLUMN IF EXISTS approved,
    DROP COLUMN IF EXISTS odk_central_url CASCADE,
    DROP COLUMN IF EXISTS odk_central_user CASCADE,
    DROP COLUMN IF EXISTS odk_central_password CASCADE;

-- Commit the transaction
COMMIT;
