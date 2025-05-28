-- ## Migration to:
-- * Add public.communitytype enum.
-- * Add public.organisation.community_type field.

-- Start a transaction
BEGIN;

-- Create communitytype enum if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'communitytype') THEN
    CREATE TYPE public.communitytype AS ENUM (
      'OSM_COMMUNITY',
      'COMPANY',
      'NON_PROFIT',
      'UNIVERSITY',
      'OTHER'
    );
  END IF;
END $$;
ALTER TYPE public.communitytype OWNER TO fmtm;

-- Add the community_type column to organisations table
ALTER TABLE IF EXISTS public.organisations
ADD COLUMN IF NOT EXISTS community_type public.communitytype
DEFAULT 'OSM_COMMUNITY';

-- Commit the transaction
COMMIT;
