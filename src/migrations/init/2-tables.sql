CREATE TABLE public.users (
    sub character varying NOT NULL,
    username character varying,
    is_admin boolean DEFAULT FALSE,
    name character varying,
    city character varying,
    country character varying,
    profile_img character varying,
    email_address character varying,
    registered_at timestamp with time zone DEFAULT now(),
    last_login_at timestamp with time zone DEFAULT now()
);
ALTER TABLE public.users OWNER TO fmtm;


CREATE TABLE public.template_xlsforms (
    id integer NOT NULL,
    title character varying,
    xls bytea
);
ALTER TABLE public.template_xlsforms OWNER TO fmtm;
CREATE SEQUENCE public.template_xlsforms_id_seq
AS integer
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;
ALTER TABLE public.template_xlsforms_id_seq OWNER TO fmtm;
ALTER SEQUENCE public.template_xlsforms_id_seq
OWNED BY public.template_xlsforms.id;
-- Autoincrement PK
ALTER TABLE ONLY public.template_xlsforms
ALTER COLUMN id SET DEFAULT nextval(
    'public.template_xlsforms_id_seq'::regclass
);


CREATE TABLE public.projects (
    id integer NOT NULL,
    field_mapping_app public.fieldmappingapp DEFAULT 'QField',
    external_project_instance_url character varying,
    external_project_id integer,
    external_project_username character varying,
    external_project_password_encrypted character varying,
    created_by_sub character varying,
    project_name character varying,
    description character varying,
    slug character varying,
    location_str character varying,
    outline public.GEOMETRY (GEOMETRY, 4326),
    status public.projectstatus NOT NULL DEFAULT 'DRAFT',
    visibility public.projectvisibility NOT NULL DEFAULT 'PUBLIC',
    xlsform_content bytea,
    hashtags character varying [],
    custom_tms_url character varying,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);
ALTER TABLE public.projects OWNER TO fmtm;
CREATE SEQUENCE public.projects_id_seq
AS integer
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;
ALTER TABLE public.projects_id_seq OWNER TO fmtm;
ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;
-- Autoincrement PK
ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval(
    'public.projects_id_seq'::regclass
);
