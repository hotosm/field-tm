-- ## Migration to:
-- * Add field user.profile_img (str).

-- Start a transaction
BEGIN;

ALTER TABLE IF EXISTS public.users
ADD COLUMN IF NOT EXISTS profile_img VARCHAR;
-- Commit the transaction
COMMIT;
