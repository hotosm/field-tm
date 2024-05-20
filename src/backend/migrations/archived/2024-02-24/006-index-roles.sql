-- ## Migration to:
-- * Index public.user_roles table.
-- * Index public.organisation_managers table.

-- Start a transaction
BEGIN;

CREATE INDEX IF NOT EXISTS idx_user_roles ON public.user_roles USING btree (
    project_id, user_id
);
CREATE INDEX IF NOT EXISTS idx_org_managers ON public.organisation_managers
USING btree (
    user_id, organisation_id
);

-- Commit the transaction
COMMIT;
