-- Track asynchronous task-splitting state for the advanced HTMX flow.
-- The split runs as a background asyncio task (no proxy/statement timeout)
-- and the frontend polls these columns to know when to render the preview.
--
-- Status is derived implicitly from the two columns:
--   both NULL              -> running (or never started)
--   split_error populated  -> failed
--   split_result populated -> ready for preview
--
-- On Accept, split_result_geojson is moved into task_areas_geojson and
-- this column is cleared so the proposed-vs-accepted overlap window
-- closes immediately.
ALTER TABLE IF EXISTS projects
ADD COLUMN IF NOT EXISTS split_error text,
ADD COLUMN IF NOT EXISTS split_result_geojson jsonb;
