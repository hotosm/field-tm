-- Start a transaction

BEGIN;

ALTER TABLE public.organisations
DROP COLUMN IF EXISTS associated_email;

ALTER TABLE public.projects
DROP CONSTRAINT IF EXISTS projects_geo_restrict_distance_meters_check,
DROP COLUMN IF EXISTS new_geom_type,
DROP COLUMN IF EXISTS geo_restrict_distance_meters,
DROP COLUMN IF EXISTS geo_restrict_force_error;

DROP TYPE IF EXISTS public.geomtype;

-- Commit the transaction
COMMIT;
