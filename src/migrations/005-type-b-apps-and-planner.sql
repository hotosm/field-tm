-- Type B mapping apps (task files only, no sync) for the app picker (#3135).
ALTER TYPE fieldmappingapp ADD VALUE IF NOT EXISTS 'EveryDoor';
ALTER TYPE fieldmappingapp ADD VALUE IF NOT EXISTS 'StreetComplete';
ALTER TYPE fieldmappingapp ADD VALUE IF NOT EXISTS 'CoMapeo';
ALTER TYPE fieldmappingapp ADD VALUE IF NOT EXISTS 'CoMaps';
ALTER TYPE fieldmappingapp ADD VALUE IF NOT EXISTS 'Panoramax';
ALTER TYPE fieldmappingapp ADD VALUE IF NOT EXISTS 'SketchMap';
ALTER TYPE fieldmappingapp ADD VALUE IF NOT EXISTS 'ChatMap';
ALTER TYPE fieldmappingapp ADD VALUE IF NOT EXISTS 'Other';

-- Task splitting moved to the browser-based task planner, so the server-side
-- split job state (004) is no longer used.
ALTER TABLE IF EXISTS projects
DROP COLUMN IF EXISTS split_error,
DROP COLUMN IF EXISTS split_result_geojson;
