-- Load tables shared with PGLite mapper frontend
\i './shared/2-tables.sql'


-- Note we use UUID for interoperability with external databases,
-- such as PGLite or other microservices
CREATE TABLE public.background_tasks (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    name character varying,
    project_id integer,
    status public.backgroundtaskstatus NOT NULL DEFAULT 'PENDING',
    message character varying
);
ALTER TABLE public.background_tasks OWNER TO fmtm;


-- Note we use UUID for interoperability with external databases,
-- such as PGLite or other microservices
CREATE TABLE public.basemaps (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    project_id integer,
    status public.backgroundtaskstatus NOT NULL,
    url character varying,
    tile_source character varying,
    background_task_id character varying,
    created_at timestamp with time zone DEFAULT now()
);
ALTER TABLE public.basemaps OWNER TO fmtm;


CREATE TABLE public.organisation_managers (
    organisation_id integer NOT NULL,
    user_sub character varying NOT NULL
);
ALTER TABLE public.organisation_managers OWNER TO fmtm;


CREATE TABLE public.organisations (
    id integer NOT NULL,
    name character varying(512) NOT NULL,
    slug character varying(255) NOT NULL,
    logo character varying,
    description character varying,
    url character varying,
    type public.organisationtype DEFAULT 'FREE',
    community_type public.communitytype DEFAULT 'OSM_COMMUNITY',
    created_by character varying,
    associated_email character varying,
    approved BOOLEAN DEFAULT false,
    odk_central_url character varying,
    odk_central_user character varying,
    odk_central_password character varying,
    created_at timestamp with time zone NOT NULL DEFAULT now()
);
ALTER TABLE public.organisations OWNER TO fmtm;
CREATE SEQUENCE public.organisations_id_seq
AS integer
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;
ALTER TABLE public.organisations_id_seq OWNER TO fmtm;
ALTER SEQUENCE public.organisations_id_seq OWNED BY public.organisations.id;
-- Autoincrement PK
ALTER TABLE ONLY public.organisations ALTER COLUMN id SET DEFAULT nextval(
    'public.organisations_id_seq'::regclass
);


CREATE TABLE public.projects (
    id integer NOT NULL,
    organisation_id integer,
    odkid integer,
    author_sub character varying,
    name character varying,
    short_description character varying,
    description character varying,
    per_task_instructions character varying,
    slug character varying,
    location_str character varying,
    outline public.GEOMETRY (GEOMETRY, 4326),
    status public.projectstatus NOT NULL DEFAULT 'DRAFT',
    total_tasks integer,
    osm_category character varying,
    xlsform_content bytea,
    odk_form_id character varying,
    odk_form_xml xml,
    visibility public.projectvisibility NOT NULL DEFAULT 'PUBLIC',
    mapper_level public.mappinglevel NOT NULL DEFAULT 'INTERMEDIATE',
    priority public.projectpriority DEFAULT 'MEDIUM',
    featured boolean DEFAULT false,
    due_date timestamp with time zone,
    changeset_comment character varying,
    odk_central_url character varying,
    odk_central_user character varying,
    odk_central_password character varying,
    odk_token character varying,
    data_extract_url character varying,
    task_split_type public.tasksplittype,
    task_split_dimension smallint,
    task_num_buildings smallint,
    hashtags character varying [],
    custom_tms_url character varying,
    geo_restrict_force_error boolean DEFAULT false,
    geo_restrict_distance_meters int2 DEFAULT 50 CHECK (
        geo_restrict_distance_meters >= 0
    ),
    primary_geom_type public.geomtype DEFAULT 'POLYGON',
    new_geom_type public.geomtype DEFAULT 'POLYGON',
    use_odk_collect boolean DEFAULT false,
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
-- Table field comments
COMMENT ON COLUMN public.projects.geo_restrict_force_error
IS 'Prevent users from creating new geometries far away from current location';
COMMENT ON COLUMN public.projects.geo_restrict_distance_meters
IS 'Specify how many meters the user can be from new point before error shown';
COMMENT ON COLUMN public.projects.primary_geom_type IS
'Main geom type being mapped in this project';
COMMENT ON COLUMN public.projects.new_geom_type IS
'Geom type used for drawing new geoms, e.g. existing: polygons, new: points';
COMMENT ON COLUMN public.projects.use_odk_collect IS
'Override whether this project uses ODK Collect (vs default webforms)';


CREATE TABLE public.tasks (
    id integer NOT NULL,
    project_id integer NOT NULL,
    project_task_index integer,
    outline public.GEOMETRY (POLYGON, 4326),
    feature_count integer
);
ALTER TABLE public.tasks OWNER TO fmtm;
CREATE SEQUENCE public.tasks_id_seq
AS integer
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;
ALTER TABLE public.tasks_id_seq OWNER TO fmtm;
ALTER SEQUENCE public.tasks_id_seq OWNED BY public.tasks.id;
-- Autoincrement PK
ALTER TABLE ONLY public.tasks ALTER COLUMN id SET DEFAULT nextval(
    'public.tasks_id_seq'::regclass
);


CREATE TABLE public.user_roles (
    user_sub character varying NOT NULL,
    project_id integer NOT NULL,
    role public.projectrole NOT NULL DEFAULT 'MAPPER'
);
ALTER TABLE public.user_roles OWNER TO fmtm;


CREATE TABLE public.users (
    sub character varying NOT NULL,
    username character varying,
    role public.userrole NOT NULL DEFAULT 'MAPPER',
    name character varying,
    city character varying,
    country character varying,
    profile_img character varying,
    email_address character varying,
    is_email_verified boolean DEFAULT false,
    is_expert boolean DEFAULT false,
    mapping_level public.mappinglevel NOT NULL DEFAULT 'BEGINNER',
    tasks_mapped integer NOT NULL DEFAULT 0,
    tasks_validated integer NOT NULL DEFAULT 0,
    tasks_invalidated integer NOT NULL DEFAULT 0,
    projects_mapped integer [],
    api_key character varying,
    registered_at timestamp with time zone DEFAULT now(),
    last_login_at timestamp with time zone DEFAULT now()
);
ALTER TABLE public.users OWNER TO fmtm;


CREATE TABLE IF NOT EXISTS public.user_invites (
    token UUID DEFAULT gen_random_uuid(),
    project_id integer NOT NULL,
    role public.projectrole NOT NULL DEFAULT 'MAPPER',
    osm_username VARCHAR,
    email VARCHAR,
    expires_at timestamp with time zone DEFAULT now() + interval '7 days',
    used_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);
ALTER TABLE public.user_invites OWNER TO fmtm;


CREATE TABLE public.xlsforms (
    id integer NOT NULL,
    title character varying,
    xls bytea
);
ALTER TABLE public.xlsforms OWNER TO fmtm;
CREATE SEQUENCE public.xlsforms_id_seq
AS integer
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;
ALTER TABLE public.xlsforms_id_seq OWNER TO fmtm;
ALTER SEQUENCE public.xlsforms_id_seq OWNED BY public.xlsforms.id;
-- Autoincrement PK
ALTER TABLE ONLY public.xlsforms ALTER COLUMN id SET DEFAULT nextval(
    'public.xlsforms_id_seq'::regclass
);


CREATE TABLE IF NOT EXISTS public.project_teams (
    team_id UUID DEFAULT gen_random_uuid(),
    team_name VARCHAR UNIQUE,
    project_id INTEGER NOT NULL
);
ALTER TABLE public.project_teams OWNER TO fmtm;
CREATE SEQUENCE public.team_name_seq
AS integer
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;
ALTER SEQUENCE public.team_name_seq OWNED BY public.project_teams.team_name;
-- Autoincrement PK
ALTER TABLE ONLY public.project_teams
ALTER COLUMN team_name SET DEFAULT (
    'Team ' || nextval('public.team_name_seq'::regclass)
);


CREATE TABLE IF NOT EXISTS public.project_team_users (
    team_id UUID,
    user_sub character varying NOT NULL
);
ALTER TABLE public.project_team_users OWNER TO fmtm;
