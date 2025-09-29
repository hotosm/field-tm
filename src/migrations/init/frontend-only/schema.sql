-- This table is an aggregate of data returned by two API endpoints:
--   - /projects/summaries, for the main info, plus computed fields
--     such as num_contributors.
--   - /projects/{id} for more detailed info.
-- The table is updated as the endpoints are called, rather than
-- synced directly via Electric.
-- This is because we need some of the aggregate fields generated
-- on the API, plus we can't
-- sync the `outline` field of type Geometry (PGLite does not support
-- PostGIS yet).

-- Tables
CREATE TABLE public.projects (
    id integer NOT NULL,
    organisation_id integer,
    field_mapping_app public.fieldmappingapp DEFAULT 'FieldTM',
    name character varying,
    short_description character varying,
    description character varying,
    per_task_instructions character varying,
    location_str character varying,
    status public.projectstatus NOT NULL DEFAULT 'DRAFT',
    total_tasks integer,
    odk_form_id character varying,
    odk_token character varying,
    odk_form_xml xml,
    visibility public.projectvisibility NOT NULL DEFAULT 'PUBLIC',
    mapper_level public.mappinglevel NOT NULL DEFAULT 'INTERMEDIATE',
    priority public.projectpriority DEFAULT 'MEDIUM',
    featured boolean DEFAULT false,
    data_extract_url character varying,
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
    updated_at timestamp with time zone DEFAULT now(),
    -- Extras / calculated by API
    organisation_logo character varying,
    outline JSONB,
    centroid JSONB,
    tasks JSONB,
    num_contributors integer,
    total_submissions integer
);

CREATE TABLE public.api_submissions (
    id integer NOT NULL,
    user_sub character varying,
    url character varying NOT NULL,
    method character varying DEFAULT 'POST' CHECK (
        method IN (
            'HEAD',
            'GET',
            'POST',
            'PATCH',
            'PUT',
            'DELETE'
        )
    ),
    content_type character varying DEFAULT 'application/json' CHECK (
        content_type IN (
            'application/json',
            'multipart/form-data',
            'application/xml',
            'text/plain'
        )
    ),
    payload JSONB,
    headers JSONB,
    status character varying DEFAULT 'PENDING' CHECK (
        status IN ('PENDING', 'RECEIVED', 'FAILED')
    ),
    retry_count integer DEFAULT 0,
    error character varying,
    queued_at timestamp with time zone DEFAULT now(),
    last_attempt_at timestamp with time zone,
    success_at timestamp with time zone
);
-- As we don't copy data in, need to autoincrement the id
CREATE SEQUENCE public.api_submissions_seq
AS integer
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;
ALTER TABLE public.api_submissions_seq OWNER TO fmtm;
ALTER SEQUENCE public.api_submissions_seq OWNED BY public.api_submissions.id;
-- Autoincrement PK
ALTER TABLE ONLY public.api_submissions ALTER COLUMN id SET DEFAULT nextval(
    'public.api_submissions_seq'::regclass
);

-- Replica of the api_submissions to store failed submissions
CREATE TABLE api_failures (LIKE api_submissions INCLUDING ALL);


-- Constraints
ALTER TABLE ONLY public.projects
ADD CONSTRAINT projects_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.api_submissions
ADD CONSTRAINT api_submissions_pkey PRIMARY KEY (id);


-- Indexes (we do not index on geometry field, as no postgis)
CREATE INDEX idx_projects_organisation_id
ON public.projects USING btree (
    organisation_id
);
