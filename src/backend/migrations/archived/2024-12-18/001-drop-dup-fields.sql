-- ## Migration to:
-- * Drop fields that duplicate logic
-- * Mostly `_by` fields, where we have a user id.
-- *   The info for mapping / validating is stored in the task_history already.
-- * Also removes the redundant geometry_geojson and project_task_name fields

-- Start a transaction
BEGIN;

-- Drop locked_by, mapped_by, validated_by
ALTER TABLE ONLY public.tasks DROP CONSTRAINT IF EXISTS fk_users_locked;
ALTER TABLE ONLY public.tasks DROP CONSTRAINT IF EXISTS fk_users_mapper;
ALTER TABLE ONLY public.tasks DROP CONSTRAINT IF EXISTS fk_users_validator;

ALTER TABLE ONLY public.tasks DROP COLUMN IF EXISTS locked_by;
ALTER TABLE ONLY public.tasks DROP COLUMN IF EXISTS mapped_by;
ALTER TABLE ONLY public.tasks DROP COLUMN IF EXISTS validated_by;
ALTER TABLE ONLY public.tasks DROP COLUMN IF EXISTS geometry_geojson;
ALTER TABLE ONLY public.tasks DROP COLUMN IF EXISTS project_task_name;

DROP INDEX IF EXISTS ix_tasks_locked_by;
DROP INDEX IF EXISTS ix_tasks_mapped_by;
DROP INDEX IF EXISTS ix_tasks_validated_by;

-- Drop duplicated info in task_status field
ALTER TABLE ONLY public.tasks DROP COLUMN IF EXISTS task_status;

-- Commit the transaction
COMMIT;
