ALTER TABLE ONLY public.users
ADD CONSTRAINT users_pkey PRIMARY KEY (sub);

ALTER TABLE ONLY public.projects
ADD CONSTRAINT projects_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.user_invites
ADD CONSTRAINT user_invites_pkey PRIMARY KEY (token);

ALTER TABLE ONLY public.template_xlsforms
ADD CONSTRAINT xlsforms_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.template_xlsforms
ADD CONSTRAINT xlsforms_title_key UNIQUE (title);
