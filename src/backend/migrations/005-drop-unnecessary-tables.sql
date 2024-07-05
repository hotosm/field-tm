-- ## Migration to:
-- * Drop task_mapping_issues
-- * Drop task_invalidation_history
-- * Drop user_licenses
-- * Drop licenses
-- * Drop mapping_issue_categories
-- * Drop project_teams
-- * Drop project_chat
-- * Drop teams
-- * Drop related enums and linked columns

-- Start a transaction
BEGIN;

DROP INDEX IF EXISTS public.ix_task_mapping_issues_task_history_id;
DROP TABLE IF EXISTS public.task_mapping_issues;
DROP SEQUENCE IF EXISTS public.task_mapping_issues_id_seq;

DROP INDEX IF EXISTS public.idx_task_validation_history_composite;
DROP INDEX IF EXISTS public.idx_task_validation_mapper_status_composite;
DROP INDEX IF EXISTS public.idx_task_validation_validator_status_composite;
DROP TABLE IF EXISTS public.task_invalidation_history;
DROP SEQUENCE IF EXISTS public.task_invalidation_history_id_seq;

ALTER TABLE public.projects
DROP COLUMN IF EXISTS license_id;

DROP TABLE IF EXISTS public.user_licenses;
DROP TABLE IF EXISTS public.licenses;
DROP SEQUENCE IF EXISTS public.licenses_id_seq;

DROP TABLE IF EXISTS public.mapping_issue_categories;
DROP SEQUENCE IF EXISTS public.mapping_issue_categories_id_seq;

DROP TABLE IF EXISTS public.project_teams;
DROP INDEX IF EXISTS ix_project_chat_project_id;
DROP TABLE IF EXISTS public.project_chat;
DROP SEQUENCE IF EXISTS public.project_chat_id_seq;
DROP TABLE IF EXISTS public.teams;
DROP SEQUENCE IF EXISTS public.teams_id_seq;

ALTER TABLE public.projects
DROP COLUMN IF EXISTS mapping_permission,
DROP COLUMN IF EXISTS validation_permission;
DROP TYPE IF EXISTS public.validationpermission;
DROP TYPE IF EXISTS public.mappingpermission;
DROP TYPE IF EXISTS public.teamvisibility;

-- Commit the transaction
COMMIT;
