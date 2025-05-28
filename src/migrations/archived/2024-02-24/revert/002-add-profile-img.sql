-- Start a transaction
BEGIN;

-- Remove the profile_img column from the public.users table
ALTER TABLE IF EXISTS public.users
DROP COLUMN IF EXISTS profile_img;

-- Commit the transaction
COMMIT;
