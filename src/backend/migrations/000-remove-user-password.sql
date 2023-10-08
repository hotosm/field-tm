-- ## Migration to remove password field from public.users (replaced with OSM OAuth)


-- ## Apply Migration
-- Start a transaction
BEGIN;
-- Drop the 'password' column if it exists
ALTER TABLE IF EXISTS public.users
DROP COLUMN IF EXISTS password;
-- Commit the transaction
COMMIT;


-- ## Revert Migration (comment above, uncomment below)
-- -- Start a transaction
-- BEGIN;
-- -- Add the 'password' column back if it doesn't exist
-- ALTER TABLE public.users
-- ADD COLUMN IF NOT EXISTS password character varying;
-- -- Commit the transaction
-- COMMIT;
