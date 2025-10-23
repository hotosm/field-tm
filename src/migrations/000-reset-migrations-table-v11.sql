-- ## Migration reset the _migrations table.

-- Start a transaction
BEGIN;
-- Delete all records
DELETE FROM public._migrations;
-- Commit the transaction
COMMIT;
