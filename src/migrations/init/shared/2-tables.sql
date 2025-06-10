CREATE TABLE public._migrations (
    script_name text,
    date_executed timestamp with time zone
);
ALTER TABLE public._migrations OWNER TO fmtm;


-- Note we use UUID for interoperability with external databases,
-- such as PGLite or other microservices
CREATE TABLE public.task_events (
    event_id UUID NOT NULL DEFAULT gen_random_uuid(),
    event public.taskevent NOT NULL,
    task_id integer NOT NULL,
    project_id integer,
    user_sub character varying,
    team_id UUID,
    username character varying,
    state public.mappingstate,
    comment text,
    created_at timestamp with time zone NOT NULL DEFAULT now()
);
ALTER TABLE public.task_events OWNER TO fmtm;


CREATE TABLE public.odk_entities (
    entity_id UUID NOT NULL,
    status public.entitystate NOT NULL,
    project_id integer NOT NULL,
    task_id integer,
    osm_id bigint,
    submission_ids character varying,
    -- This a javarosa geom string
    geometry character varying,
    created_by character varying
);
ALTER TABLE public.odk_entities OWNER TO fmtm;
