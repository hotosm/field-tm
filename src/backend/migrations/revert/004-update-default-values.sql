-- ## Migration to:
-- * Remove default values from respective fields in the table.

-- Start a transaction
BEGIN;

-- Revert changes in mapping_issue_categories table
ALTER TABLE public.mapping_issue_categories
ALTER COLUMN archived DROP DEFAULT;

-- Revert changes in mbtiles_path table
ALTER TABLE public.mbtiles_path
ALTER COLUMN created_at DROP DEFAULT;

-- Revert changes in project_chat table
ALTER TABLE public.project_chat
ALTER COLUMN time_stamp DROP DEFAULT;

-- Revert changes in projects table
ALTER TABLE public.projects
ALTER COLUMN created DROP DEFAULT,
ALTER COLUMN last_updated DROP DEFAULT,
ALTER COLUMN status DROP DEFAULT,
ALTER COLUMN mapper_level DROP DEFAULT,
ALTER COLUMN priority DROP DEFAULT,
ALTER COLUMN featured DROP DEFAULT,
ALTER COLUMN mapping_permission DROP DEFAULT,
ALTER COLUMN validation_permission DROP DEFAULT;

-- Revert changes in task_history table
ALTER TABLE public.task_history
ALTER COLUMN action_date DROP DEFAULT;

-- Revert changes in task_invalidation_history table
ALTER TABLE public.task_invalidation_history
ALTER COLUMN is_closed DROP DEFAULT,
ALTER COLUMN updated_date DROP DEFAULT;

-- Revert changes in task_invalidation_history_id_seq table
ALTER TABLE public.task_invalidation_history_id_seq
ALTER COLUMN task_status DROP DEFAULT;

-- Revert changes in teams table
ALTER TABLE public.teams
ALTER COLUMN invite_only DROP DEFAULT,
ALTER COLUMN visibility DROP DEFAULT;

-- Revert changes in user_roles table
ALTER TABLE public.user_roles
ALTER COLUMN role DROP DEFAULT;

-- Revert changes in users table
ALTER TABLE public.users
ALTER COLUMN role DROP DEFAULT,
ALTER COLUMN is_email_verified DROP DEFAULT,
ALTER COLUMN is_expert DROP DEFAULT,
ALTER COLUMN mapping_level DROP DEFAULT,
ALTER COLUMN tasks_mapped DROP DEFAULT,
ALTER COLUMN tasks_validated DROP DEFAULT,
ALTER COLUMN tasks_invalidated DROP DEFAULT,
ALTER COLUMN date_registered DROP DEFAULT,
ALTER COLUMN last_validation_date DROP DEFAULT;

-- Commit the transaction
COMMIT;
