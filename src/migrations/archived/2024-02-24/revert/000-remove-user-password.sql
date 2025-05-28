-- Start a transaction
BEGIN;
-- Add the 'password' column back if it doesn't exist
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS password character varying;
-- Commit the transaction
COMMIT;
