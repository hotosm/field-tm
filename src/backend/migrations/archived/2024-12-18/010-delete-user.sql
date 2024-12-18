-- ## Migration to:
-- * Enable user data deletion

-- Start a transaction
BEGIN;

-- Add column 'username' to 'task_events' table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='task_events' AND column_name='username'
    ) THEN
        ALTER TABLE public.task_events
        ADD COLUMN username VARCHAR;
    END IF;
END $$;

-- Make 'user_id' nullable in 'task_events' table
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='task_events' AND column_name='user_id' AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE public.task_events
        ALTER COLUMN user_id DROP NOT NULL;
    END IF;
END $$;

-- Make 'author_id' nullable in 'projects' table
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='projects' AND column_name='author_id' AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE public.projects
        ALTER COLUMN author_id DROP NOT NULL;
    END IF;
END $$;

-- Commit the transaction
COMMIT;
