-- ## Migration to:
-- * As use_odk_collect override field to projects

-- Start a transaction
BEGIN;

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'use_odk_collect'
    ) THEN
        ALTER TABLE public.projects ADD COLUMN use_odk_collect boolean DEFAULT false;
    END IF;
END $$;

-- Commit the transaction
COMMIT;
