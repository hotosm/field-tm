-- ## Migration to:
-- * Add the created_by column to the organisations table

-- Start a transaction

BEGIN;

ALTER TABLE organisations
ADD COLUMN IF NOT EXISTS created_by INTEGER;

-- Commit the transaction
COMMIT;
