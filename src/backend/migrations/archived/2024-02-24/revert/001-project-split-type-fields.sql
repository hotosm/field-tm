-- Start a transaction
BEGIN;
-- Revert task_split_type type
DO $$ 
BEGIN
    -- Check if the column exists
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'task_split_type') THEN
        -- Alter the column if it exists
        EXECUTE '
            ALTER TABLE public.projects
            ALTER COLUMN task_split_type
            TYPE VARCHAR
            USING task_split_type::VARCHAR
        ';
    END IF;
END $$;
-- Remove extra fields
ALTER TABLE IF EXISTS public.projects
DROP COLUMN IF EXISTS task_split_dimension,
DROP COLUMN IF EXISTS task_num_buildings;
-- Remove enum
DROP TYPE IF EXISTS public.tasksplittype;
-- Commit the transaction
COMMIT;
