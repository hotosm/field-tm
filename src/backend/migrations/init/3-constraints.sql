-- Load tables shared with PGLite mapper frontend
\i './shared/3-constraints.sql'


ALTER TABLE ONLY public.background_tasks
ADD CONSTRAINT background_tasks_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.basemaps
ADD CONSTRAINT basemaps_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.organisation_managers
ADD CONSTRAINT organisation_user_key UNIQUE (organisation_id, user_sub);

ALTER TABLE ONLY public.organisations
ADD CONSTRAINT organisations_name_key UNIQUE (name);

ALTER TABLE ONLY public.organisations
ADD CONSTRAINT organisations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.organisations
ADD CONSTRAINT organisations_slug_key UNIQUE (slug);

ALTER TABLE ONLY public.projects
ADD CONSTRAINT projects_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.tasks
ADD CONSTRAINT tasks_pkey PRIMARY KEY (id, project_id);

ALTER TABLE ONLY public.user_roles
ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_sub, project_id);

ALTER TABLE ONLY public.users
ADD CONSTRAINT users_pkey PRIMARY KEY (sub);

ALTER TABLE ONLY public.user_invites
ADD CONSTRAINT user_invites_pkey PRIMARY KEY (token);

ALTER TABLE ONLY public.xlsforms
ADD CONSTRAINT xlsforms_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.xlsforms
ADD CONSTRAINT xlsforms_title_key UNIQUE (title);

ALTER TABLE ONLY public.project_teams
ADD CONSTRAINT project_teams_pkey PRIMARY KEY (team_id);

ALTER TABLE ONLY public.project_team_users
ADD CONSTRAINT project_team_users_pkey PRIMARY KEY (team_id, user_sub);
