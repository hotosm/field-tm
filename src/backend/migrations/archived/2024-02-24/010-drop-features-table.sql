-- ## Migration to:
-- * Drop features table.

-- Start a transaction
BEGIN;

DROP TABLE IF EXISTS public.features CASCADE;
DROP SEQUENCE IF EXISTS public.features_id_seq;
DROP INDEX IF EXISTS idx_features_composite;
DROP INDEX IF EXISTS idx_features_geometry;

-- Commit the transaction
COMMIT;
