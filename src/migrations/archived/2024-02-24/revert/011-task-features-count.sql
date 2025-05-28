-- Start a transaction
BEGIN;

ALTER TABLE IF EXISTS public.tasks
RENAME COLUMN feature_count TO initial_feature_count;

-- Commit the transaction
COMMIT;
