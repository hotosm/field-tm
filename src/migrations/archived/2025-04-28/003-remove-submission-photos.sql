-- ## Migration to:
-- * Drop submission_photos table (replaced by ODK implementation)

-- Start a transaction
BEGIN;

DROP TABLE IF EXISTS public.submission_photos;

-- Commit the transaction
COMMIT;
