-- ## Migration to:
-- * Add public.projectrole enum.
-- * Update the user_roles table to use the enum

-- Start a transaction
BEGIN;

-- Create projectrole enum if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'projectrole') THEN
    CREATE TYPE public.projectrole AS ENUM (
    'MAPPER',
    'VALIDATOR',
    'FIELD_MANAGER',
    'ASSOCIATE_PROJECT_MANAGER',
    'PROJECT_MANAGER'
    );
  END IF;
END $$;
ALTER TYPE public.projectrole OWNER TO fmtm;

ALTER TABLE public.user_roles
ALTER COLUMN role TYPE VARCHAR(24);

ALTER TABLE public.user_roles
ALTER COLUMN role TYPE public.projectrole USING role::public.projectrole;

-- Commit the transaction
COMMIT;
