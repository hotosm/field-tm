CREATE TYPE public.fieldmappingapp AS ENUM ('QField', 'ODK', 'FieldTM');
ALTER TYPE public.fieldmappingapp OWNER TO fmtm;

CREATE TYPE public.projectstatus AS ENUM (
    'ARCHIVED',
    'PUBLISHED',
    'DRAFT',
    'COMPLETED'
);
ALTER TYPE public.projectstatus OWNER TO fmtm;

CREATE TYPE public.projectvisibility AS ENUM (
    'PUBLIC',
    'PRIVATE'
);
ALTER TYPE public.projectvisibility OWNER TO fmtm;
