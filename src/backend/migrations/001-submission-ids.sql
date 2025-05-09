-- ## Migration to:
-- * Add osm_id integer field to odk_entities
-- * Add submission_ids string field to odk_entities

-- Start a transaction
BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'odk_entities' AND column_name = 'osm_id'
    ) THEN
        ALTER TABLE public.odk_entities ADD COLUMN osm_id integer;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'odk_entities' AND column_name = 'submission_ids'
    ) THEN
        ALTER TABLE public.odk_entities ADD COLUMN submission_ids character varying;
    END IF;
END $$;

-- Commit the transaction
COMMIT;
