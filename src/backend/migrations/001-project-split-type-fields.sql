-- ## Migration to:
-- * Change project.task_split_type str --> int.
-- * Add field project.task_split_dimension (int).
-- * Add field project.task_num_buildings (int).



-- ## Apply Migration
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
ALTER TYPE public.mappinglevel OWNER TO fmtm;

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



-- -- ## Revert Migration (comment above, uncomment below)
-- -- Start a transaction
-- BEGIN;
-- -- Revert task_split_type type
-- DO $$ 
-- BEGIN
--     -- Check if the column exists
--     IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'task_split_type') THEN
--         -- Alter the column if it exists
--         EXECUTE '
--             ALTER TABLE public.projects
--             ALTER COLUMN task_split_type
--             TYPE VARCHAR
--             USING task_split_type::VARCHAR
--         ';
--     END IF;
-- END $$;
-- -- Remove extra fields
-- ALTER TABLE IF EXISTS public.projects
--     DROP COLUMN IF EXISTS task_split_dimension,
--     DROP COLUMN IF EXISTS task_num_buildings;
-- -- Remove enum
-- DROP TYPE IF EXISTS public.tasksplittype;
-- -- Commit the transaction
-- COMMIT;
