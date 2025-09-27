-- Migration to add field_mapping_app field to projects table

BEGIN;

-- Create enum type if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typname = 'fieldmappingapp'
          AND n.nspname = 'public'
    ) THEN
        CREATE TYPE public.fieldmappingapp AS ENUM ('QField', 'ODK', 'FieldTM');
    END IF;
END $$;

-- Add column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'projects'
          AND column_name = 'field_mapping_app'
    ) THEN
        ALTER TABLE public.projects
        ADD COLUMN field_mapping_app public.fieldmappingapp;
    END IF;
END $$;

COMMIT;
