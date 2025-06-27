-- ## Migration add some extra fields.
-- * Add geo_restrict_distance_meters and geo_restrict_force_error to projects.
-- * Add new_geom_type to projects.
-- * Add associated_email to organisations.

-- Related issues:
-- https://github.com/hotosm/field-tm/issues/1985#issuecomment-2577342507
-- https://github.com/hotosm/field-tm/issues/1979
-- https://github.com/hotosm/field-tm/issues/2066

-- Start a transaction

BEGIN;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'geomtype') THEN
        CREATE TYPE public.geomtype AS ENUM ('POINT', 'POLYLINE', 'POLYGON');
    END IF;
END $$;
ALTER TYPE public.geomstatus OWNER TO fmtm;

ALTER TABLE public.organisations
ADD COLUMN IF NOT EXISTS associated_email
character varying;

ALTER TABLE public.projects
ADD COLUMN IF NOT EXISTS new_geom_type
public.geomtype
DEFAULT 'POINT',
ADD COLUMN IF NOT EXISTS geo_restrict_distance_meters
int2
DEFAULT 50
CHECK (geo_restrict_distance_meters >= 0),
ADD COLUMN IF NOT EXISTS geo_restrict_force_error
BOOLEAN
DEFAULT false;

-- Also update the fields from previous migration
DROP INDEX IF EXISTS idx_geometrylog;
DROP INDEX IF EXISTS idx_geom_gin;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'geometrylog' AND column_name = 'geom') THEN
        ALTER TABLE public.geometrylog RENAME COLUMN geom TO geojson;
        ALTER TABLE public.geometrylog ALTER COLUMN geojson TYPE JSONB USING geojson::jsonb;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_geometrylog_geojson
ON geometrylog USING gin (geojson);

-- Commit the transaction
COMMIT;
