-- ## Migration to:
-- * Update tasks.initial_feature_count --> tasks.feature_count.

-- Start a transaction
BEGIN;

ALTER TABLE IF EXISTS public.tasks
    RENAME COLUMN initial_feature_count TO feature_count;

-- Commit the transaction
COMMIT;
