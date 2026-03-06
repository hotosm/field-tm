-- ## Migration reset the _migrations table.

-- Start a transaction
BEGIN;
-- Delete all records
DELETE FROM _migrations;
-- Commit the transaction
COMMIT;
