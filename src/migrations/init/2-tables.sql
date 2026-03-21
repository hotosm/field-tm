CREATE TABLE users (
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
ALTER TABLE users OWNER TO current_user;


CREATE TABLE template_xlsforms (
    id integer NOT NULL,
    title character varying,
    xls bytea
);
ALTER TABLE template_xlsforms OWNER TO current_user;
CREATE SEQUENCE template_xlsforms_id_seq
AS integer
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;
ALTER TABLE template_xlsforms_id_seq OWNER TO current_user;
ALTER SEQUENCE template_xlsforms_id_seq
OWNED BY template_xlsforms.id;
-- Autoincrement PK
ALTER TABLE ONLY template_xlsforms
ALTER COLUMN id SET DEFAULT nextval(
    'template_xlsforms_id_seq'::regclass
);


CREATE TABLE projects (
    id integer NOT NULL,
    field_mapping_app fieldmappingapp DEFAULT 'QField',
    external_project_instance_url character varying,
    external_project_id character varying,
    external_project_username character varying,
    external_project_password_encrypted character varying,
    created_by_sub character varying,
    project_name character varying,
    description character varying,
    slug character varying,
    location_str character varying,
    outline GEOMETRY (GEOMETRY, 4326),
    status projectstatus NOT NULL DEFAULT 'DRAFT',
    visibility projectvisibility NOT NULL DEFAULT 'PUBLIC',
    xlsform_content bytea,
    data_extract_geojson JSONB,
    task_areas_geojson JSONB,
    hashtags character varying [],
    custom_tms_url character varying,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);
ALTER TABLE projects OWNER TO current_user;
CREATE SEQUENCE projects_id_seq
AS integer
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;
ALTER TABLE projects_id_seq OWNER TO current_user;
ALTER SEQUENCE projects_id_seq OWNED BY projects.id;
-- Autoincrement PK
ALTER TABLE ONLY projects ALTER COLUMN id SET DEFAULT nextval(
    'projects_id_seq'::regclass
);


CREATE TABLE user_roles (
    user_sub character varying NOT NULL,
    project_id integer NOT NULL,
    role projectrole NOT NULL DEFAULT 'MAPPER'
);
ALTER TABLE user_roles OWNER TO current_user;


-- Temporary job state for QGIS project generation (shared between containers)
CREATE TABLE qgis_jobs (
    job_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    xlsform BYTEA,
    features JSONB,
    tasks JSONB,
    output_files JSONB
);
ALTER TABLE qgis_jobs OWNER TO current_user;


CREATE TABLE api_keys (
    id integer NOT NULL,
    user_sub character varying NOT NULL,
    key_hash character varying NOT NULL,
    name character varying,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    last_used_at timestamp with time zone,
    is_active boolean NOT NULL DEFAULT TRUE
);
ALTER TABLE api_keys OWNER TO current_user;
CREATE SEQUENCE api_keys_id_seq
AS integer
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;
ALTER TABLE api_keys_id_seq OWNER TO current_user;
ALTER SEQUENCE api_keys_id_seq OWNED BY api_keys.id;
-- Autoincrement PK
ALTER TABLE ONLY api_keys ALTER COLUMN id SET DEFAULT nextval(
    'api_keys_id_seq'::regclass
);
