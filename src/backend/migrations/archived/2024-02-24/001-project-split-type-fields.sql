-- ## Migration to:
-- * Change project.task_split_type str --> int.
-- * Add field project.task_split_dimension (int).
-- * Add field project.task_num_buildings (int).

-- Start a transaction
BEGIN;
-- Create task_split_type enum if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tasksplittype') THEN
    CREATE TYPE public.tasksplittype AS ENUM (
      'DIVIDE_ON_SQUARE',
      'CHOOSE_AREA_AS_TASK',
      'TASK_SPLITTING_ALGORITHM'
    );
  END IF;
END $$;
ALTER TYPE public.tasksplittype OWNER TO fmtm;

-- Update task_split_type
DO $$ 
BEGIN
    -- Check if the column exists
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'task_split_type') THEN
        -- Alter the column if it exists
        EXECUTE '
            ALTER TABLE public.projects
            ALTER COLUMN task_split_type
            TYPE public.tasksplittype
            USING task_split_type::tasksplittype
        ';
    END IF;
END $$;

-- Add extra columns
ALTER TABLE IF EXISTS public.projects
ADD COLUMN IF NOT EXISTS task_split_dimension SMALLINT,
ADD COLUMN IF NOT EXISTS task_num_buildings SMALLINT;
-- Commit the transaction
COMMIT;
