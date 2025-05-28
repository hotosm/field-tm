-- ## Migration to:
-- * As use_odk_collect override field to projects

-- Start a transaction
BEGIN;

DROP MATERIALIZED VIEW IF EXISTS mv_project_stats;

-- Commit the transaction
COMMIT;
