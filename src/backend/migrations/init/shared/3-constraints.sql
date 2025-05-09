ALTER TABLE public._migrations
ADD CONSTRAINT _migrations_pkey PRIMARY KEY (script_name);

ALTER TABLE ONLY public.task_events
ADD CONSTRAINT task_events_pkey PRIMARY KEY (event_id);

ALTER TABLE ONLY public.odk_entities
ADD CONSTRAINT odk_entities_pkey PRIMARY KEY (entity_id);

ALTER TABLE ONLY public.geometrylog
ADD CONSTRAINT geometrylog_pkey PRIMARY KEY (id);
