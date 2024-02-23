-- ## Migration to:
-- * Update tasks.initial_feature_count --> tasks.feature_count.

-- Start a transaction
BEGIN;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'tasks' AND column_name = 'initial_feature_count') THEN
        ALTER TABLE public.tasks RENAME COLUMN initial_feature_count TO feature_count;
    END IF;
END $$;

-- Commit the transaction
COMMIT;
