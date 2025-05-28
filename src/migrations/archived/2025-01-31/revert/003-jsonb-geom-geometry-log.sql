-- Start a transaction
BEGIN;

-- Drop the newly created index if needed
DROP INDEX IF EXISTS idx_geom_gin;

-- Change the 'geom' column back to its original type (geometry)
-- Using ST_GeomFromGeoJSON() to convert jsonb (GeoJSON) back to geometry
ALTER TABLE geometrylog
ALTER COLUMN geom TYPE geometry USING ST_GEOMFROMGEOJSON(geom::text);

-- This step creates a new temporary 'id_int' column to store the integer IDs
ALTER TABLE geometrylog ADD COLUMN id_int INTEGER;

WITH numbered_rows AS (
    SELECT
        id,
        ROW_NUMBER() OVER () AS new_id
    FROM geometrylog
)

UPDATE geometrylog
SET id_int = numbered_rows.new_id
FROM numbered_rows
WHERE geometrylog.id = numbered_rows.id;

-- Now, drop the old UUID 'id' column
ALTER TABLE geometrylog DROP COLUMN id;

-- Rename the new 'id_int' column back to 'id'
ALTER TABLE geometrylog RENAME COLUMN id_int TO id;
ALTER TABLE geometrylog ADD PRIMARY KEY (id);

CREATE INDEX IF NOT EXISTS idx_geometrylog ON geometrylog USING gist (geom);

-- Commit the transaction
COMMIT;
