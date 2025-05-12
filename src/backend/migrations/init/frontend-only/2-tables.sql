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

CREATE TABLE public.projects (
    id integer NOT NULL,
    organisation_id integer,
    name character varying,
    short_description character varying,
    description character varying,
    per_task_instructions character varying,
    location_str character varying,
    status public.projectstatus NOT NULL DEFAULT 'DRAFT',
    total_tasks integer,
    odk_form_id character varying,
    visibility public.projectvisibility NOT NULL DEFAULT 'PUBLIC',
    mapper_level public.mappinglevel NOT NULL DEFAULT 'INTERMEDIATE',
    priority public.projectpriority DEFAULT 'MEDIUM',
    featured boolean DEFAULT false,
    odk_token character varying,
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
