-- ## Migration to update geom column to jsonb type and int id to uuid.

-- Start a transaction

BEGIN;
-- drop existing indexes
DROP INDEX IF EXISTS idx_geometrylog;

-- Change the 'geom' column to jsonb type
ALTER TABLE geometrylog
ALTER COLUMN geom TYPE jsonb USING geom::jsonb;

-- Alter the 'id' column to UUID
-- set the default value using gen_random_uuid()
-- First, drop the default if it's currently not a UUID
ALTER TABLE geometrylog
ALTER COLUMN id DROP DEFAULT;

-- Change the column type to UUID and set the default value
ALTER TABLE geometrylog
ALTER COLUMN id TYPE UUID USING gen_random_uuid(),
ALTER COLUMN id SET DEFAULT gen_random_uuid();

CREATE INDEX IF NOT EXISTS idx_geom_gin ON geometrylog USING gist (geom);

-- Commit the transaction
COMMIT;
