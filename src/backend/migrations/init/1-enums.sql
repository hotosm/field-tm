-- Load tables shared with PGLite mapper frontend
\i './shared/1-enums.sql'


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
    'MEDIUM',
    'LOW',
    'HIGH',
    'URGENT'
);
ALTER TYPE public.projectpriority OWNER TO fmtm;

CREATE TYPE public.projectstatus AS ENUM (
    'ARCHIVED',
    'PUBLISHED',
    'DRAFT'
);
ALTER TYPE public.projectstatus OWNER TO fmtm;

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

CREATE TYPE public.geomtype AS ENUM (
    'POINT',
    'POLYLINE',
    'POLYGON'
);
ALTER TYPE public.geomtype OWNER TO fmtm;
