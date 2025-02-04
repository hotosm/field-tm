-- ## Migration to enable SFCGAL for usage of PostGIS StraightSkeleton function.

-- Start a transaction
BEGIN;
CREATE EXTENSION IF NOT EXISTS postgis_sfcgal WITH SCHEMA public;
-- Commit the transaction
COMMIT;
