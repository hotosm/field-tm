-- ## Migration to remove password field from public.users
-- ## (replaced with OSM OAuth)

-- Start a transaction
BEGIN;
-- Drop the 'password' column if it exists
ALTER TABLE IF EXISTS public.users
DROP COLUMN IF EXISTS password;
-- Commit the transaction
COMMIT;
