ALTER TABLE ONLY users
ADD CONSTRAINT users_pkey PRIMARY KEY (sub);

ALTER TABLE ONLY projects
ADD CONSTRAINT projects_pkey PRIMARY KEY (id);

ALTER TABLE ONLY template_xlsforms
ADD CONSTRAINT xlsforms_pkey PRIMARY KEY (id);

ALTER TABLE ONLY template_xlsforms
ADD CONSTRAINT xlsforms_title_key UNIQUE (title);

ALTER TABLE ONLY user_roles
ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_sub, project_id);
