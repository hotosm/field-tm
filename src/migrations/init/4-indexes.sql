-- Load tables shared with PGLite mapper frontend
\i './shared/4-indexes.sql'


CREATE INDEX idx_projects_outline ON public.projects USING gist (outline);
CREATE INDEX idx_projects_mapper_level
ON public.projects USING btree (
    mapper_level
);
CREATE INDEX idx_projects_organisation_id
ON public.projects USING btree (
    organisation_id
);
CREATE INDEX idx_tasks_outline ON public.tasks USING gist (outline);
CREATE INDEX idx_tasks_composite
ON public.tasks USING btree (
    id, project_id
);
CREATE INDEX idx_user_roles ON public.user_roles USING btree (
    project_id, user_sub
);
CREATE INDEX idx_org_managers ON public.organisation_managers USING btree (
    organisation_id, user_sub
);
CREATE INDEX idx_user_invites_project
ON public.user_invites USING btree (
    project_id
);
CREATE INDEX idx_project_team_users_team_id
ON public.project_team_users USING btree (
    team_id
);

CREATE INDEX IF NOT EXISTS idx_submission_daily_counts_user_date
ON public.submission_daily_counts (user_sub, submission_date);

CREATE INDEX IF NOT EXISTS idx_submission_daily_counts_user_project_date
ON public.submission_daily_counts (user_sub, project_id, submission_date);

CREATE INDEX IF NOT EXISTS idx_submission_stats_cache_user
ON public.submission_stats_cache (user_sub);

CREATE INDEX IF NOT EXISTS idx_submission_stats_cache_user_project
ON public.submission_stats_cache (user_sub, project_id);

CREATE INDEX IF NOT EXISTS project_external_urls_project_source_idx
ON project_external_urls (project_id, source);
