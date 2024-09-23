-- ## Migration to:
-- * Rename projects.form_xls --> projects.xlsform_content
-- * Remove projects.form_config_file until required
-- * Add missed foreign keys to submission_photos
-- * Remove public.xforms table, moving odk_form_id to public.projects
-- Decided to remove the XForms table as projects likely always have a
--      1:1 relationship with xforms (spwoodcock)

-- Start a transaction
BEGIN;

-- Add foreign keys to submission_photos table, if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_project_id'
          AND table_name = 'submission_photos'
    ) THEN
        ALTER TABLE ONLY public.submission_photos
        ADD CONSTRAINT fk_project_id FOREIGN KEY (project_id)
        REFERENCES public.projects (id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_tasks'
          AND table_name = 'submission_photos'
    ) THEN
        ALTER TABLE ONLY public.submission_photos
        ADD CONSTRAINT fk_tasks FOREIGN KEY (
            task_id, project_id
        ) REFERENCES public.tasks (id, project_id);
    END IF;
END $$;

-- Update public.projects table
ALTER TABLE public.projects
-- Remove form_config_file column
DROP COLUMN IF EXISTS form_config_file,
-- Add odk_form_id if not exists
ADD COLUMN IF NOT EXISTS odk_form_id VARCHAR;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'form_xls') THEN
        ALTER TABLE public.projects
            RENAME COLUMN form_xls TO xlsform_content;  -- Rename form_xls to xlsform_content
    END IF;
END $$;

-- Migrate odk_form_id data from xforms to projects
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'xforms' 
          AND column_name = 'odk_form_id'
    ) THEN
        -- Perform data migration if odk_form_id exists in xforms
        UPDATE public.projects p
        SET odk_form_id = x.odk_form_id
        FROM public.xforms x
        WHERE x.project_id = p.id
          AND p.odk_form_id IS NULL;  -- Avoid overwriting existing values
    END IF;
END $$;

-- Drop public.xforms table if it exists
DROP TABLE IF EXISTS public.xforms;
DROP SEQUENCE IF EXISTS public.xforms_id_seq;

-- Commit the transaction
COMMIT;
