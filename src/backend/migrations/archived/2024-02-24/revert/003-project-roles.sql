-- Start a transaction
BEGIN;

-- Revert user_roles table changes
ALTER TABLE public.user_roles ALTER COLUMN role TYPE VARCHAR(24);

ALTER TABLE public.user_roles ALTER COLUMN role TYPE public.userrole
USING role::public.userrole;

-- Drop the public.projectrole enum
DROP TYPE IF EXISTS public.projectrole;

-- Commit the transaction
COMMIT;
