BEGIN;

-- Remove the community_type column from organisations table
ALTER TABLE public.organisations
DROP COLUMN IF EXISTS community_type;

-- Drop the communitytype enum
DROP TYPE IF EXISTS public.communitytype;

-- Commit the transaction
COMMIT;
