-- ## Migration to:
-- * Remove projects.extract_completed_count
-- * Remove projects.xform_title
-- * Add projects.xform_category
-- * Remove projects.xform_title foreign key constraint

-- Start a transaction
BEGIN;

-- Remove extract_completed_count
ALTER TABLE IF EXISTS public.projects
DROP COLUMN IF EXISTS extract_completed_count;

-- Remove xform_title
ALTER TABLE IF EXISTS public.projects
DROP COLUMN IF EXISTS xform_title;

-- Add xform_category
ALTER TABLE IF EXISTS public.projects
ADD COLUMN IF NOT EXISTS xform_category character varying;

-- Remove xform_title foreign key to public.xforms
DO $$
DECLARE
    constraint_exists BOOLEAN;
BEGIN
    -- Check if the foreign key constraint exists
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.constraint_column_usage 
        WHERE constraint_name = 'fk_xform'
    ) INTO constraint_exists;

    IF constraint_exists THEN
        -- Drop the foreign key constraint
        ALTER TABLE public.projects
        DROP CONSTRAINT fk_xform;
        
        RAISE NOTICE 'Foreign key constraint "fk_xform" dropped successfully.';
    ELSE
        RAISE NOTICE 'Foreign key constraint "fk_xform" does not exist.';
    END IF;
END $$;

-- Commit the transaction
COMMIT;
