-- ## Migration to:
-- * Drop and recreate some indexes.
-- * Add some new indexes for task_events.


-- Start a transaction
BEGIN;

-- Drop some existing indexes

DROP INDEX IF EXISTS idx_geometry;
DROP INDEX IF EXISTS ix_projects_mapper_level;
DROP INDEX IF EXISTS ix_projects_organisation_id;
DROP INDEX IF EXISTS ix_tasks_project_id;
DROP INDEX IF EXISTS ix_users_id;
DROP INDEX IF EXISTS idx_task_history_composite;
DROP INDEX IF EXISTS idx_task_history_project_id_user_id;
DROP INDEX IF EXISTS ix_task_history_project_id;
DROP INDEX IF EXISTS ix_task_history_user_id;
DROP INDEX IF EXISTS idx_task_history_date;

-- Create new indexes
CREATE INDEX IF NOT EXISTS idx_projects_mapper_level
ON public.projects USING btree (
    mapper_level
);
CREATE INDEX IF NOT EXISTS idx_projects_organisation_id
ON public.projects USING btree (
    organisation_id
);
CREATE INDEX IF NOT EXISTS idx_tasks_composite
ON public.tasks USING btree (
    id, project_id
);
CREATE INDEX IF NOT EXISTS idx_task_event_composite
ON public.task_events USING btree (
    task_id, project_id
);
CREATE INDEX IF NOT EXISTS idx_task_event_project_user
ON public.task_events USING btree (
    user_id, project_id
);
CREATE INDEX IF NOT EXISTS idx_task_event_project_id
ON public.task_events USING btree (
    task_id, project_id
);
CREATE INDEX IF NOT EXISTS idx_task_event_user_id
ON public.task_events USING btree (
    task_id, user_id
);
CREATE INDEX IF NOT EXISTS idx_task_event_date
ON public.task_events USING btree (
    task_id, created_at
);

-- Commit the transaction
COMMIT;
