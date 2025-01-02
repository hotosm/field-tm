-- ## Migration to delete geometrylog table.

-- Start a transaction

BEGIN;

DROP TABLE IF EXISTS geometrylog;

-- Commit the transaction

COMMIT;
