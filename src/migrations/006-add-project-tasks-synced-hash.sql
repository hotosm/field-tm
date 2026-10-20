-- Hash of the task geometries last synced to ODK or QField, so re-sync can
-- tell assignment-only edits from task area changes.
ALTER TABLE IF EXISTS projects
ADD COLUMN IF NOT EXISTS tasks_synced_hash character varying;
