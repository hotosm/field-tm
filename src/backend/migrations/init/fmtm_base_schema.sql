--
-- PostgreSQL database dump
--

-- Dumped from database version 14.9
-- Dumped by pg_dump version 15.3 (Debian 15.3-0+deb12u1)

-- Started on 2023-10-05 12:55:27 UTC


-- Setup

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER SCHEMA public OWNER TO fmtm;


-- PostGIS

CREATE SCHEMA tiger;
ALTER SCHEMA tiger OWNER TO fmtm;

CREATE SCHEMA tiger_data;
ALTER SCHEMA tiger_data OWNER TO fmtm;

CREATE SCHEMA topology;
ALTER SCHEMA topology OWNER TO fmtm;

CREATE EXTENSION IF NOT EXISTS fuzzystrmatch WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder WITH SCHEMA tiger;
CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;


-- Enums

CREATE TYPE public.backgroundtaskstatus AS ENUM (
    'PENDING',
    'FAILED',
    'RECEIVED',
    'SUCCESS'
);
ALTER TYPE public.backgroundtaskstatus OWNER TO fmtm;

CREATE TYPE public.mappinglevel AS ENUM (
    'BEGINNER',
    'INTERMEDIATE',
    'ADVANCED'
);
ALTER TYPE public.mappinglevel OWNER TO fmtm;

CREATE TYPE public.organisationtype AS ENUM (
    'FREE',
    'DISCOUNTED',
    'FULL_FEE'
);
ALTER TYPE public.organisationtype OWNER TO fmtm;

CREATE TYPE public.projectpriority AS ENUM (
    'URGENT',
    'HIGH',
    'MEDIUM',
    'LOW'
);
ALTER TYPE public.projectpriority OWNER TO fmtm;

CREATE TYPE public.projectstatus AS ENUM (
    'ARCHIVED',
    'PUBLISHED',
    'DRAFT'
);
ALTER TYPE public.projectstatus OWNER TO fmtm;

CREATE TYPE public.taskaction AS ENUM (
    'RELEASED_FOR_MAPPING',
    'LOCKED_FOR_MAPPING',
    'MARKED_MAPPED',
    'LOCKED_FOR_VALIDATION',
    'VALIDATED',
    'MARKED_INVALID',
    'MARKED_BAD',
    'SPLIT_NEEDED',
    'RECREATED',
    'COMMENT'
);
ALTER TYPE public.taskaction OWNER TO fmtm;

CREATE TYPE public.taskstatus AS ENUM (
    'READY',
    'LOCKED_FOR_MAPPING',
    'MAPPED',
    'LOCKED_FOR_VALIDATION',
    'VALIDATED',
    'INVALIDATED',
    'BAD',
    'SPLIT',
    'ARCHIVED'
);
ALTER TYPE public.taskstatus OWNER TO fmtm;

CREATE TYPE public.userrole AS ENUM (
    'READ_ONLY',
    'MAPPER',
    'ADMIN'
);
ALTER TYPE public.userrole OWNER TO fmtm;

CREATE TYPE public.projectrole AS ENUM (
    'MAPPER',
    'VALIDATOR',
    'FIELD_MANAGER',
    'ASSOCIATE_PROJECT_MANAGER',
    'PROJECT_MANAGER'
);
ALTER TYPE public.projectrole OWNER TO fmtm;

CREATE TYPE public.projectvisibility AS ENUM (
    'PUBLIC',
    'PRIVATE',
    'INVITE_ONLY'
);
ALTER TYPE public.projectvisibility OWNER TO fmtm;

CREATE TYPE public.tasksplittype AS ENUM (
    'DIVIDE_ON_SQUARE',
    'CHOOSE_AREA_AS_TASK',
    'TASK_SPLITTING_ALGORITHM'
);
ALTER TYPE public.tasksplittype OWNER TO fmtm;

CREATE TYPE public.communitytype AS ENUM (
    'OSM_COMMUNITY',
    'COMPANY',
    'NON_PROFIT',
    'UNIVERSITY',
    'OTHER'
);
ALTER TYPE public.communitytype OWNER TO fmtm;


-- Extra

SET default_tablespace = '';
SET default_table_access_method = heap;


-- Tables

CREATE TABLE IF NOT EXISTS public._migrations (
    date_executed TIMESTAMP,
    script_name TEXT
);
ALTER TABLE public._migrations OWNER TO fmtm;


CREATE TABLE public.background_tasks (
    id character varying NOT NULL,
    name character varying,
    project_id integer,
    status public.backgroundtaskstatus NOT NULL,
    message character varying
);
ALTER TABLE public.background_tasks OWNER TO fmtm;


CREATE TABLE public.mbtiles_path (
    id integer NOT NULL,
    project_id integer,
    status public.backgroundtaskstatus NOT NULL,
    path character varying,
    tile_source character varying,
    background_task_id character varying,
    created_at timestamp without time zone DEFAULT now()
);
ALTER TABLE public.mbtiles_path OWNER TO fmtm;
CREATE SEQUENCE public.mbtiles_path_id_seq
AS integer
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;
ALTER TABLE public.mbtiles_path_id_seq OWNER TO fmtm;
ALTER SEQUENCE public.mbtiles_path_id_seq OWNED BY public.mbtiles_path.id;


CREATE TABLE public._migrations (
    script_name text,
    date_executed timestamp without time zone
);
ALTER TABLE public._migrations OWNER TO fmtm;


CREATE TABLE public.organisation_managers (
    organisation_id integer NOT NULL,
    user_id bigint NOT NULL
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
    created_by integer,
    approved BOOLEAN DEFAULT false,
    odk_central_url character varying,
    odk_central_user character varying,
    odk_central_password character varying
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


CREATE TABLE public.project_info (
    project_id integer NOT NULL,
    project_id_str character varying,
    name character varying(512),
    short_description character varying,
    description character varying,
    text_searchable tsvector,
    per_task_instructions character varying
);
ALTER TABLE public.project_info OWNER TO fmtm;


CREATE TABLE public.projects (
    id integer NOT NULL,
    organisation_id integer,
    odkid integer,
    author_id bigint NOT NULL,
    created timestamp without time zone NOT NULL DEFAULT now(),
    project_name_prefix character varying,
    task_type_prefix character varying,
    location_str character varying,
    outline public.GEOMETRY (POLYGON, 4326),
    last_updated timestamp without time zone DEFAULT now(),
    status public.projectstatus NOT NULL DEFAULT 'DRAFT',
    total_tasks integer,
    xform_category character varying,
    xlsform_content bytea,
    odk_form_id character varying,
    visibility public.projectvisibility NOT NULL DEFAULT 'PUBLIC',
    mapper_level public.mappinglevel NOT NULL DEFAULT 'INTERMEDIATE',
    priority public.projectpriority DEFAULT 'MEDIUM',
    featured boolean DEFAULT false,
    due_date timestamp without time zone,
    changeset_comment character varying,
    osmcha_filter_id character varying,
    imagery character varying,
    osm_preset character varying,
    odk_preset character varying,
    josm_preset character varying,
    id_presets character varying [],
    extra_id_params character varying,
    centroid public.GEOMETRY (POINT, 4326),
    odk_central_url character varying,
    odk_central_user character varying,
    odk_central_password character varying,
    odk_token character varying,
    data_extract_type character varying,
    data_extract_url character varying,
    task_split_type public.tasksplittype,
    task_split_dimension smallint,
    task_num_buildings smallint,
    hashtags character varying []
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


CREATE TABLE public.task_history (
    id integer NOT NULL,
    project_id integer,
    task_id integer NOT NULL,
    action public.taskaction NOT NULL,
    action_text character varying,
    action_date timestamp without time zone NOT NULL DEFAULT now(),
    user_id bigint NOT NULL
);
ALTER TABLE public.task_history OWNER TO fmtm;
CREATE SEQUENCE public.task_history_id_seq
AS integer
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;
ALTER TABLE public.task_history_id_seq OWNER TO fmtm;
ALTER SEQUENCE public.task_history_id_seq OWNED BY public.task_history.id;


CREATE TABLE public.tasks (
    id integer NOT NULL,
    project_id integer NOT NULL,
    project_task_index integer,
    project_task_name character varying,
    outline public.GEOMETRY (POLYGON, 4326),
    geometry_geojson character varying,
    feature_count integer,
    task_status public.taskstatus DEFAULT 'READY',
    locked_by bigint,
    mapped_by bigint,
    validated_by bigint
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


CREATE TABLE public.user_roles (
    user_id bigint NOT NULL,
    project_id integer NOT NULL,
    role public.projectrole NOT NULL DEFAULT 'MAPPER'
);
ALTER TABLE public.user_roles OWNER TO fmtm;


CREATE TABLE public.users (
    id bigint NOT NULL,
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
    date_registered timestamp without time zone DEFAULT now(),
    last_validation_date timestamp without time zone DEFAULT now()
);
ALTER TABLE public.users OWNER TO fmtm;

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

CREATE TABLE public.submission_photos (
    id integer NOT NULL,
    project_id integer NOT NULL,
    -- Note this is not public.tasks, but an ODK task_id
    task_id integer NOT NULL,
    submission_id character varying NOT NULL,
    s3_path character varying NOT NULL
);
ALTER TABLE public.submission_photos OWNER TO fmtm;
CREATE SEQUENCE public.submission_photos_id_seq
AS integer
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;
ALTER TABLE public.submission_photos_id_seq OWNER TO fmtm;
ALTER SEQUENCE public.submission_photos_id_seq
OWNED BY public.submission_photos.id;

-- nextval for primary keys (autoincrement)

ALTER TABLE ONLY public.mbtiles_path ALTER COLUMN id SET DEFAULT nextval(
    'public.mbtiles_path_id_seq'::regclass
);
ALTER TABLE ONLY public.organisations ALTER COLUMN id SET DEFAULT nextval(
    'public.organisations_id_seq'::regclass
);
ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval(
    'public.projects_id_seq'::regclass
);
ALTER TABLE ONLY public.task_history ALTER COLUMN id SET DEFAULT nextval(
    'public.task_history_id_seq'::regclass
);
ALTER TABLE ONLY public.tasks ALTER COLUMN id SET DEFAULT nextval(
    'public.tasks_id_seq'::regclass
);
ALTER TABLE ONLY public.xlsforms ALTER COLUMN id SET DEFAULT nextval(
    'public.xlsforms_id_seq'::regclass
);
ALTER TABLE ONLY public.submission_photos ALTER COLUMN id SET DEFAULT nextval(
    'public.submission_photos_id_seq'::regclass
);


-- Constraints for primary keys

ALTER TABLE public._migrations
ADD CONSTRAINT _migrations_pkey PRIMARY KEY (script_name);

ALTER TABLE ONLY public.background_tasks
ADD CONSTRAINT background_tasks_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.mbtiles_path
ADD CONSTRAINT mbtiles_path_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.organisation_managers
ADD CONSTRAINT organisation_user_key UNIQUE (organisation_id, user_id);

ALTER TABLE ONLY public.organisations
ADD CONSTRAINT organisations_name_key UNIQUE (name);

ALTER TABLE ONLY public.organisations
ADD CONSTRAINT organisations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.organisations
ADD CONSTRAINT organisations_slug_key UNIQUE (slug);

ALTER TABLE ONLY public.project_info
ADD CONSTRAINT project_info_pkey PRIMARY KEY (project_id);

ALTER TABLE ONLY public.projects
ADD CONSTRAINT projects_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.task_history
ADD CONSTRAINT task_history_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.tasks
ADD CONSTRAINT tasks_pkey PRIMARY KEY (id, project_id);

ALTER TABLE ONLY public.user_roles
ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, project_id);

ALTER TABLE ONLY public.users
ADD CONSTRAINT users_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.users
ADD CONSTRAINT users_username_key UNIQUE (username);

ALTER TABLE ONLY public.xlsforms
ADD CONSTRAINT xlsforms_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.xlsforms
ADD CONSTRAINT xlsforms_title_key UNIQUE (title);

ALTER TABLE ONLY public.submission_photos
ADD CONSTRAINT submission_photos_pkey PRIMARY KEY (id);

-- Indexing

CREATE INDEX idx_geometry ON public.projects USING gist (outline);
CREATE INDEX idx_projects_centroid ON public.projects USING gist (centroid);
CREATE INDEX idx_projects_outline ON public.projects USING gist (outline);
CREATE INDEX idx_task_history_composite ON public.task_history USING btree (
    task_id, project_id
);
CREATE INDEX idx_task_history_project_id_user_id ON public.task_history
USING btree (
    user_id, project_id
);
CREATE INDEX idx_tasks_outline ON public.tasks USING gist (outline);
CREATE INDEX ix_projects_mapper_level ON public.projects USING btree (
    mapper_level
);
CREATE INDEX ix_projects_organisation_id ON public.projects USING btree (
    organisation_id
);
CREATE INDEX ix_task_history_project_id ON public.task_history USING btree (
    project_id
);
CREATE INDEX ix_task_history_user_id ON public.task_history USING btree (
    user_id
);
CREATE INDEX ix_tasks_locked_by ON public.tasks USING btree (locked_by);
CREATE INDEX ix_tasks_mapped_by ON public.tasks USING btree (mapped_by);
CREATE INDEX ix_tasks_project_id ON public.tasks USING btree (project_id);
CREATE INDEX ix_tasks_validated_by ON public.tasks USING btree (validated_by);
CREATE INDEX ix_users_id ON public.users USING btree (id);
CREATE INDEX textsearch_idx ON public.project_info USING btree (
    text_searchable
);
CREATE INDEX idx_user_roles ON public.user_roles USING btree (
    project_id, user_id
);
CREATE INDEX idx_org_managers ON public.organisation_managers USING btree (
    user_id, organisation_id
);

-- Foreign keys

ALTER TABLE ONLY public.projects
ADD CONSTRAINT fk_organisations FOREIGN KEY (
    organisation_id
) REFERENCES public.organisations (id);

ALTER TABLE ONLY public.task_history
ADD CONSTRAINT fk_tasks FOREIGN KEY (
    task_id, project_id
) REFERENCES public.tasks (id, project_id);

ALTER TABLE ONLY public.projects
ADD CONSTRAINT fk_users FOREIGN KEY (author_id) REFERENCES public.users (id);

ALTER TABLE ONLY public.task_history
ADD CONSTRAINT fk_users FOREIGN KEY (user_id) REFERENCES public.users (id);

ALTER TABLE ONLY public.tasks
ADD CONSTRAINT fk_users_locked FOREIGN KEY (
    locked_by
) REFERENCES public.users (id);

ALTER TABLE ONLY public.tasks
ADD CONSTRAINT fk_users_mapper FOREIGN KEY (
    mapped_by
) REFERENCES public.users (id);

ALTER TABLE ONLY public.tasks
ADD CONSTRAINT fk_users_validator FOREIGN KEY (
    validated_by
) REFERENCES public.users (id);

ALTER TABLE ONLY public.organisation_managers
ADD CONSTRAINT organisation_managers_organisation_id_fkey FOREIGN KEY (
    organisation_id
) REFERENCES public.organisations (id);

ALTER TABLE ONLY public.organisation_managers
ADD CONSTRAINT organisation_managers_user_id_fkey FOREIGN KEY (
    user_id
) REFERENCES public.users (id);

ALTER TABLE ONLY public.project_info
ADD CONSTRAINT project_info_project_id_fkey FOREIGN KEY (
    project_id
) REFERENCES public.projects (id);

ALTER TABLE ONLY public.task_history
ADD CONSTRAINT task_history_project_id_fkey FOREIGN KEY (
    project_id
) REFERENCES public.projects (id);

ALTER TABLE ONLY public.tasks
ADD CONSTRAINT tasks_project_id_fkey FOREIGN KEY (
    project_id
) REFERENCES public.projects (id);

ALTER TABLE ONLY public.user_roles
ADD CONSTRAINT user_roles_project_id_fkey FOREIGN KEY (
    project_id
) REFERENCES public.projects (id);

ALTER TABLE ONLY public.user_roles
ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (
    user_id
) REFERENCES public.users (id);

ALTER TABLE ONLY public.submission_photos
ADD CONSTRAINT fk_project_id FOREIGN KEY (
    project_id
) REFERENCES public.projects (id);

-- Finalise

REVOKE USAGE ON SCHEMA public FROM public;
GRANT ALL ON SCHEMA public TO public;
