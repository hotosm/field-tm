-- Add basemap workflow state fields to projects and qgis_jobs.
ALTER TABLE IF EXISTS projects
ADD COLUMN IF NOT EXISTS basemap_stac_item_id character varying,
ADD COLUMN IF NOT EXISTS basemap_url character varying,
ADD COLUMN IF NOT EXISTS basemap_status character varying,
ADD COLUMN IF NOT EXISTS basemap_minzoom integer,
ADD COLUMN IF NOT EXISTS basemap_maxzoom integer,
ADD COLUMN IF NOT EXISTS basemap_attach_status character varying DEFAULT 'idle',
ADD COLUMN IF NOT EXISTS basemap_attach_error text,
ADD COLUMN IF NOT EXISTS basemap_attach_updated_at timestamp with time zone;

UPDATE projects
SET basemap_attach_status = 'idle'
WHERE basemap_attach_status IS NULL;

ALTER TABLE IF EXISTS qgis_jobs
ADD COLUMN IF NOT EXISTS operation character varying NOT NULL DEFAULT 'field',
ADD COLUMN IF NOT EXISTS project_id character varying,
ADD COLUMN IF NOT EXISTS basemap_url character varying;
