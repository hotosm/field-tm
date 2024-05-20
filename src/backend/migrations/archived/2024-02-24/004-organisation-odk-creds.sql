-- ## Migration to:
-- * Add odk central credentials (str) to organisations table.
-- * Add the approved (bool) field to organisations table.
-- * Add the visibility type for project visibility level.
-- * Add the visibility field to projects table.

-- Start a transaction
BEGIN;

-- Add fields to organisations table
ALTER TABLE IF EXISTS public.organisations
ADD COLUMN IF NOT EXISTS approved BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS odk_central_url VARCHAR,
ADD COLUMN IF NOT EXISTS odk_central_user VARCHAR,
ADD COLUMN IF NOT EXISTS odk_central_password VARCHAR;

-- Create visibility enum if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'projectvisibility') THEN
    CREATE TYPE public.projectvisibility AS ENUM (
      'PUBLIC',
      'PRIVATE',
      'INVITE_ONLY'
    );
  END IF;
END $$;
ALTER TYPE public.projectvisibility OWNER TO fmtm;

-- Add field to projects table
ALTER TABLE IF EXISTS public.projects
DROP COLUMN IF EXISTS private,
ADD COLUMN IF NOT EXISTS visibility public.projectvisibility
NOT NULL DEFAULT 'PUBLIC';

-- Commit the transaction
COMMIT;
