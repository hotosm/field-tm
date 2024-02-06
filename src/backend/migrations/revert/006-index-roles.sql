-- Start a transaction
BEGIN;

DROP INDEX IF EXISTS idx_user_roles;
DROP INDEX IF EXISTS idx_org_managers;

-- Commit the transaction
COMMIT;
