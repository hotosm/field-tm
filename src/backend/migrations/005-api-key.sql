-- ## Migration add an api_key field to the users table

-- Start a transaction

BEGIN;

ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS api_key CHARACTER VARYING;

-- Commit the transaction
COMMIT;
