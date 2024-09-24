-- ## Revert Migration to:
-- * Drop submission_photos table

-- Start a transaction
BEGIN;

DROP TABLE IF EXISTS public.submission_photos;

-- Commit the transaction
COMMIT;
