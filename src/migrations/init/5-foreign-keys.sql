ALTER TABLE ONLY public.projects
ADD CONSTRAINT fk_organisations FOREIGN KEY (
    organisation_id
) REFERENCES public.organisations (id);

ALTER TABLE ONLY public.projects
ADD CONSTRAINT fk_users FOREIGN KEY (author_sub) REFERENCES public.users (sub);

ALTER TABLE ONLY public.organisation_managers
ADD CONSTRAINT organisation_managers_organisation_id_fkey FOREIGN KEY (
    organisation_id
) REFERENCES public.organisations (id);

ALTER TABLE ONLY public.organisation_managers
ADD CONSTRAINT organisation_managers_user_sub_fkey FOREIGN KEY (
    user_sub
) REFERENCES public.users (sub);

ALTER TABLE ONLY public.tasks
ADD CONSTRAINT tasks_project_id_fkey FOREIGN KEY (
    project_id
) REFERENCES public.projects (id);

ALTER TABLE ONLY public.task_events
ADD CONSTRAINT fk_projects FOREIGN KEY (
    project_id
) REFERENCES public.projects (id);

ALTER TABLE ONLY public.task_events
ADD CONSTRAINT fk_project_task_id FOREIGN KEY (
    task_id, project_id
) REFERENCES public.tasks (id, project_id);

ALTER TABLE ONLY public.task_events
ADD CONSTRAINT fk_users FOREIGN KEY (
    user_sub
) REFERENCES public.users (sub);

ALTER TABLE ONLY public.task_events
ADD CONSTRAINT fk_team_id FOREIGN KEY (
    team_id
) REFERENCES public.project_teams (team_id);

ALTER TABLE ONLY public.user_roles
ADD CONSTRAINT user_roles_project_id_fkey FOREIGN KEY (
    project_id
) REFERENCES public.projects (id);

ALTER TABLE ONLY public.user_roles
ADD CONSTRAINT user_roles_user_sub_fkey FOREIGN KEY (
    user_sub
) REFERENCES public.users (sub);

ALTER TABLE ONLY public.user_invites
ADD CONSTRAINT user_invites_project_id_fkey FOREIGN KEY (
    project_id
) REFERENCES public.projects (id);

ALTER TABLE ONLY public.project_teams
ADD CONSTRAINT fk_projects FOREIGN KEY (
    project_id
) REFERENCES public.projects (id) ON DELETE CASCADE;

ALTER TABLE ONLY public.project_team_users
ADD CONSTRAINT fk_users FOREIGN KEY (
    user_sub
) REFERENCES public.users (sub) ON DELETE CASCADE;

ALTER TABLE ONLY public.submission_daily_counts
ADD CONSTRAINT submission_daily_counts_user_sub_fkey
FOREIGN KEY (user_sub) REFERENCES public.users (sub) ON DELETE CASCADE;

ALTER TABLE ONLY public.submission_daily_counts
ADD CONSTRAINT submission_daily_counts_project_fkey
FOREIGN KEY (project_id) REFERENCES public.projects (id) ON DELETE CASCADE;

ALTER TABLE ONLY public.submission_stats_cache
ADD CONSTRAINT submission_stats_cache_user_sub_fkey
FOREIGN KEY (user_sub) REFERENCES public.users (sub) ON DELETE CASCADE;

ALTER TABLE ONLY public.submission_stats_cache
ADD CONSTRAINT submission_stats_cache_project_fkey
FOREIGN KEY (project_id) REFERENCES public.projects (id) ON DELETE CASCADE;
