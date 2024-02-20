-- Start a transaction
BEGIN;

-- Drop the column created_by
ALTER TABLE organisations
DROP COLUMN IF EXISTS created_by;

-- Commit the transaction
COMMIT;
