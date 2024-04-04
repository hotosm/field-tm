-- ## Migration to:
-- * Add xforms table to link projects with multiple forms
-- * Move field odk_token from tasks --> projects

-- Start a transaction
BEGIN;

CREATE TABLE IF NOT EXISTS public.xforms (
    id integer NOT NULL,
    project_id integer,
    odk_form_id character varying,
    category character varying
);
ALTER TABLE public.xforms OWNER TO fmtm;
CREATE SEQUENCE IF NOT EXISTS public.xforms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE public.xforms_id_seq OWNER TO fmtm;
ALTER SEQUENCE public.xforms_id_seq OWNED BY public.xforms.id;
ALTER TABLE ONLY public.xforms ALTER COLUMN id SET DEFAULT nextval('public.xforms_id_seq'::regclass);
ALTER TABLE ONLY public.xforms
    ADD CONSTRAINT xforms_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.xforms
    ADD CONSTRAINT fk_project_id FOREIGN KEY (project_id) REFERENCES public.projects(id);

-- Create field public.projects.odk_token
ALTER TABLE public.projects
    ADD COLUMN IF NOT EXISTS odk_token VARCHAR;

-- Copy the value of the first tasks.odk_token to projects.odk_token
UPDATE public.projects
SET odk_token = (
    SELECT odk_token
    FROM public.tasks
    WHERE NOT EXISTS (SELECT 1 FROM public.projects WHERE odk_token IS NOT NULL)
    LIMIT 1
)
WHERE id = (
    SELECT id
    FROM public.projects
    WHERE NOT EXISTS (SELECT 1 FROM public.projects WHERE odk_token IS NOT NULL)
    LIMIT 1
);

-- Delete the field public.tasks.odk_token
ALTER TABLE public.tasks
    DROP COLUMN IF EXISTS odk_token;

-- Commit the transaction
COMMIT;
