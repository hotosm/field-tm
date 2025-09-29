-- Load tables shared with PGLite mapper frontend
\i './shared/1-enums.sql'


CREATE TYPE public.backgroundtaskstatus AS ENUM (
    'PENDING',
    'FAILED',
    'RECEIVED',
    'SUCCESS'
);
ALTER TYPE public.backgroundtaskstatus OWNER TO fmtm;

CREATE TYPE public.organisationtype AS ENUM (
    'FREE',
    'DISCOUNTED',
    'FULL_FEE'
);
ALTER TYPE public.organisationtype OWNER TO fmtm;

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

CREATE TYPE public.fieldmappingapp AS ENUM ('QField', 'ODK', 'FieldTM');
ALTER TYPE public.fieldmappingapp OWNER TO fmtm;
