-- ## Migration to:
-- * Replace projects.xform_category with projects.osm_category
-- * Replace projects.data_extract_type with primary_geom_type
--   (to compliment new_geom_type)
-- * Default for new_geom_type to Polygon

-- Start a transaction
BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'xform_category'
    ) THEN
        ALTER TABLE public.projects RENAME COLUMN xform_category
          TO osm_category;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'data_extract_type'
    ) THEN
        ALTER TABLE public.projects RENAME COLUMN data_extract_type
          TO primary_geom_type;

        UPDATE public.projects SET primary_geom_type = NULL;

        ALTER TABLE public.projects
          ALTER COLUMN primary_geom_type
            TYPE public.geomtype
            USING primary_geom_type::public.geomtype,
          ALTER COLUMN primary_geom_type SET DEFAULT 'POLYGON';
    END IF;
END $$;

ALTER TABLE IF EXISTS public.projects
ALTER COLUMN new_geom_type SET DEFAULT 'POLYGON';

-- Commit the transaction
COMMIT;
