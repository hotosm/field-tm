-- ## Migration to:
-- * Remove the projects.centroid field, as we can generate this dynamically.
-- * Remove long overdue unused fields from public.projects.
-- * Merge contents of project_info into projects & delete project_info.
-- * Add default timestamps to organisations & task_history table.

-- Start a transaction
BEGIN;

-- Drop columns from project_info and projects
ALTER TABLE ONLY public.projects DROP COLUMN IF EXISTS centroid;
ALTER TABLE ONLY public.projects DROP COLUMN IF EXISTS osmcha_filter_id;
ALTER TABLE ONLY public.projects DROP COLUMN IF EXISTS imagery;
ALTER TABLE ONLY public.projects DROP COLUMN IF EXISTS osm_preset;
ALTER TABLE ONLY public.projects DROP COLUMN IF EXISTS odk_preset;
ALTER TABLE ONLY public.projects DROP COLUMN IF EXISTS josm_preset;
ALTER TABLE ONLY public.projects DROP COLUMN IF EXISTS id_presets;
ALTER TABLE ONLY public.projects DROP COLUMN IF EXISTS extra_id_params;

-- Add columns to projects
ALTER TABLE ONLY public.projects
ADD COLUMN IF NOT EXISTS name character varying;
ALTER TABLE ONLY public.projects
ADD COLUMN IF NOT EXISTS short_description character varying;
ALTER TABLE ONLY public.projects
ADD COLUMN IF NOT EXISTS description character varying;
ALTER TABLE ONLY public.projects
ADD COLUMN IF NOT EXISTS per_task_instructions character varying;


-- Merge contents of project_info into projects (avoid duplicates)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'project_info') THEN
        WITH merged_projects AS (
            SELECT
                pi.project_id,
                pi.name AS pi_name,
                pi.short_description AS pi_short_description,
                pi.description AS pi_description,
                pi.per_task_instructions AS pi_per_task_instructions
            FROM public.project_info pi
            LEFT JOIN public.projects p ON pi.project_id = p.id
        )
        UPDATE public.projects p
        SET
            name = mp.pi_name,
            short_description = mp.pi_short_description,
            description = mp.pi_description,
            per_task_instructions = mp.pi_per_task_instructions
        FROM merged_projects mp
        WHERE p.id = mp.project_id;
    END IF;
END $$;

-- Drop project_info table
DROP TABLE IF EXISTS public.project_info;

-- Rename projects.project_name_prefix --> projects.slug
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'project_name_prefix') THEN
        ALTER TABLE public.projects RENAME COLUMN project_name_prefix TO slug;
    END IF;
END $$;

-- Check if the column 'action_date' already exists and has no default value
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'task_history' 
          AND column_name = 'action_date'
          AND column_default IS NULL
    ) THEN
        ALTER TABLE task_history 
        ALTER COLUMN action_date SET DEFAULT NOW();
    END IF;
END $$;

-- Check if the column 'created_at' exists in 'organisations',
-- and create it if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'organisations' 
          AND column_name = 'created_at'
    ) THEN
        ALTER TABLE organisations 
        ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
    END IF;
END $$;

-- Commit the transaction
COMMIT;
