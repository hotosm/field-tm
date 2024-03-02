-- Start a transaction
BEGIN;

-- Add the 'extract_complete_count' column if it doesn't exist
ALTER TABLE IF EXISTS public.projects
ADD COLUMN IF NOT EXISTS extract_complete_count integer;

-- Add the 'xform_title' column if it doesn't exist

ALTER TABLE IF EXISTS public.projects
ADD COLUMN IF NOT EXISTS xform_title character varying;

-- Remove the 'xform_category' column if it exists
ALTER TABLE IF EXISTS public.projects
DROP COLUMN IF EXISTS xform_category;

-- Check if the 'xform_title' foreign key constraint exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.constraint_column_usage 
        WHERE constraint_name = 'fk_xform'
    ) THEN
        RAISE NOTICE 'Foreign key constraint "fk_xform" already exists.';
    ELSE
        -- Add the 'xform_title' foreign key constraint
        ALTER TABLE ONLY public.projects
        ADD CONSTRAINT fk_xform
        FOREIGN KEY (xform_title) REFERENCES public.xlsforms(title);
        
        RAISE NOTICE 'Foreign key constraint "fk_xform" successfully added.';
    END IF;
END $$;

-- Commit the transaction
COMMIT;
