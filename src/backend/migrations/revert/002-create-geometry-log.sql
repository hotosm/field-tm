-- ## Migration to delete geometrylog table.

-- Start a transaction

BEGIN;

DROP TABLE IF EXISTS geometrylog;
DROP TYPE IF EXISTS geomstatus;

-- Commit the transaction

COMMIT;
