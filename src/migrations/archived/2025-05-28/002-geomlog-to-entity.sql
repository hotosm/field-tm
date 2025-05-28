-- ## Migration to:
-- * Add geometry string field to odk_entities for storing javarosa geom of
--   NEW features.
-- * Add is_new bool field to odk_entities to mark entity as new feature.
-- * The remainder is done in geomlog_to_entities.py.
-- * We also add the odk_form_xml field to projects table
--   (reduce Central queries)
-- * The geomlog_to_entities.py script copies across the XML content too.


-- Start a transaction
BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'odk_entities' AND column_name = 'geometry'
    ) THEN
        ALTER TABLE public.odk_entities ADD COLUMN geometry character varying;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'odk_entities' AND column_name = 'is_new'
    ) THEN
        ALTER TABLE public.odk_entities ADD COLUMN is_new boolean DEFAULT false;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'odk_form_xml'
    ) THEN
        ALTER TABLE public.projects ADD COLUMN odk_form_xml xml;
    END IF;
END $$;

-- Commit the transaction
COMMIT;
