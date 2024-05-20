-- Start a transaction
BEGIN;

-- Add qr_code table
CREATE TABLE IF NOT EXISTS public.features (
    id integer NOT NULL,
    project_id integer,
    category_title character varying,
    task_id integer,
    properties jsonb,
    geometry GEOMETRY (GEOMETRY, 4326)
);
ALTER TABLE public.features OWNER TO fmtm;

CREATE SEQUENCE public.features_id_seq
AS integer
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;
ALTER TABLE public.features_id_seq OWNER TO fmtm;
ALTER SEQUENCE public.features_id_seq OWNED BY public.features.id;

ALTER TABLE ONLY public.features ALTER COLUMN id SET DEFAULT nextval(
    'public.features_id_seq'::regclass
);
ALTER TABLE ONLY public.features
ADD CONSTRAINT features_pkey PRIMARY KEY (id);

CREATE INDEX idx_features_composite ON public.features USING btree (
    task_id, project_id
);
CREATE INDEX idx_features_geometry ON public.features USING gist (geometry);

ALTER TABLE ONLY public.features
ADD CONSTRAINT features_project_id_fkey FOREIGN KEY (
    project_id
) REFERENCES public.projects (id);
ALTER TABLE ONLY public.features
ADD CONSTRAINT fk_tasks FOREIGN KEY (
    task_id, project_id
) REFERENCES public.tasks (id, project_id);
ALTER TABLE ONLY public.features
ADD CONSTRAINT fk_xform FOREIGN KEY (
    category_title
) REFERENCES public.xlsforms (title);

-- Commit the transaction
COMMIT;
