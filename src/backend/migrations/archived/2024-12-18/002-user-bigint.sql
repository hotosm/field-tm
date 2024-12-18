-- ## Migration to:
-- * Convert the current usage of bigint for user field to int 
-- (we can still use still 2 billion user ids!)

-- Start a transaction
BEGIN;

-- First we must drop all foreign key constraints...
ALTER TABLE public.organisation_managers
DROP CONSTRAINT IF EXISTS organisation_managers_user_id_fkey;
ALTER TABLE public.projects
DROP CONSTRAINT IF EXISTS projects_author_id_fkey;
ALTER TABLE public.user_roles
DROP CONSTRAINT IF EXISTS user_roles_user_id_fkey;

-- For organisation_managers table
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='organisation_managers' 
        AND column_name='user_id' 
        AND data_type='bigint'
    ) THEN
        ALTER TABLE public.organisation_managers
        ALTER COLUMN user_id TYPE integer USING user_id::integer;
    END IF;
END $$;

-- For projects table
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='projects' 
        AND column_name='author_id' 
        AND data_type='bigint'
    ) THEN
        ALTER TABLE public.projects
        ALTER COLUMN author_id TYPE integer USING author_id::integer;
    END IF;
END $$;

-- For task_history table
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='task_history' 
        AND column_name='user_id' 
        AND data_type='bigint'
    ) THEN
        ALTER TABLE public.task_history
        ALTER COLUMN user_id TYPE integer USING user_id::integer;
    END IF;
END $$;

-- For user_roles table
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='user_roles' 
        AND column_name='user_id' 
        AND data_type='bigint'
    ) THEN
        ALTER TABLE public.user_roles
        ALTER COLUMN user_id TYPE integer USING user_id::integer;
    END IF;
END $$;

-- For users table
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='users' 
        AND column_name='id' 
        AND data_type='bigint'
    ) THEN
        ALTER TABLE public.users
        ALTER COLUMN id TYPE integer USING id::integer;
    END IF;
END $$;

-- Then add the foreign key constraints back
ALTER TABLE public.organisation_managers
ADD CONSTRAINT organisation_managers_user_id_fkey
FOREIGN KEY (user_id) REFERENCES public.users (id);
ALTER TABLE public.projects
ADD CONSTRAINT projects_author_id_fkey
FOREIGN KEY (author_id) REFERENCES public.users (id);
ALTER TABLE public.user_roles
ADD CONSTRAINT user_roles_user_id_fkey
FOREIGN KEY (user_id) REFERENCES public.users (id);

-- Commit the transaction
COMMIT;
