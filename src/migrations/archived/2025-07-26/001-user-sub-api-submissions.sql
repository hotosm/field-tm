-- ## Migration to:
-- * Add user_sub field to frontend-only api_submissions table

-- Start a transaction
BEGIN;

-- Check if table exists, and if column doesn't already exist
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' AND table_name = 'api_submissions'
  ) AND NOT EXISTS (
    SELECT FROM information_schema.columns 
    WHERE table_schema = 'public' AND table_name = 'api_submissions' AND column_name = 'user_sub'
  ) THEN
    ALTER TABLE public.api_submissions ADD COLUMN user_sub character varying;
  END IF;
END
$$;

-- Commit the transaction
COMMIT;
