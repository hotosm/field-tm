-- ## Migration to:
-- * Rename all timestamps to a consistent [field]_at syntax
-- * Drop the users.last_validation_date field we no longer need 
--    (filter task_history instead)
-- * Drop projects.task_type_prefix
-- * Convert timestamps to with time zone

-- Start a transaction
BEGIN;

-- Convert timestamps to with time zone
SET TIME ZONE 'UTC';

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'created') THEN
        ALTER TABLE public.projects RENAME COLUMN created TO created_at;
        ALTER TABLE public.projects ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'last_updated') THEN
        ALTER TABLE public.projects RENAME COLUMN last_updated TO updated_at;
        ALTER TABLE public.projects ALTER COLUMN updated_at TYPE TIMESTAMPTZ;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'date_registered') THEN
        ALTER TABLE public.users RENAME COLUMN date_registered TO registered_at;
        ALTER TABLE public.users ALTER COLUMN registered_at TYPE TIMESTAMPTZ;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = '_migrations' AND column_name = 'date_executed') THEN
        ALTER TABLE public."_migrations" ALTER COLUMN date_executed TYPE TIMESTAMPTZ;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'mbtiles_path' AND column_name = 'created_at') THEN
        ALTER TABLE public.mbtiles_path ALTER COLUMN created_at TYPE TIMESTAMPTZ;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'due_date') THEN
        ALTER TABLE public.projects ALTER COLUMN due_date TYPE TIMESTAMPTZ;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'task_history' AND column_name = 'action_date') THEN
        ALTER TABLE public.task_history ALTER COLUMN action_date TYPE TIMESTAMPTZ;
    END IF;
END $$;

-- Drop some extra columns not needed
ALTER TABLE public.users DROP COLUMN IF EXISTS last_validation_date;
ALTER TABLE public.projects DROP COLUMN IF EXISTS task_type_prefix;

-- Commit the transaction
COMMIT;
