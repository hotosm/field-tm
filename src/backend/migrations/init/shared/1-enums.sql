-- Project enums

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

CREATE TYPE public.projectvisibility AS ENUM (
    'PUBLIC',
    'PRIVATE',
    'INVITE_ONLY'
);
ALTER TYPE public.projectvisibility OWNER TO fmtm;

CREATE TYPE public.mappinglevel AS ENUM (
    'BEGINNER',
    'INTERMEDIATE',
    'ADVANCED'
);
ALTER TYPE public.mappinglevel OWNER TO fmtm;

CREATE TYPE public.geomtype AS ENUM (
    'POINT',
    'POLYLINE',
    'POLYGON'
);
ALTER TYPE public.geomtype OWNER TO fmtm;

-- Task event enums

CREATE TYPE public.taskevent AS ENUM (
    'MAP',
    'FINISH',
    'VALIDATE',
    'GOOD',
    'BAD',
    'CONFLATE',
    'SPLIT',
    'MERGE',
    'ASSIGN',
    'COMMENT',
    'RESET'
);
ALTER TYPE public.taskevent OWNER TO fmtm;

CREATE TYPE public.mappingstate AS ENUM (
    'UNLOCKED_TO_MAP',
    'LOCKED_FOR_MAPPING',
    'UNLOCKED_TO_VALIDATE',
    'LOCKED_FOR_VALIDATION',
    'UNLOCKED_DONE',
    'CONFLATED'
);
ALTER TYPE public.mappingstate OWNER TO fmtm;

CREATE TYPE public.entitystate AS ENUM (
    'READY',
    'OPENED_IN_ODK',
    'SURVEY_SUBMITTED',
    'NEW_GEOM',
    'VALIDATED',
    'MARKED_BAD'
);
ALTER TYPE public.entitystate OWNER TO fmtm;

CREATE TYPE public.geomstatus AS ENUM (
    'BAD',
    'NEW'
);
ALTER TYPE public.geomstatus OWNER TO fmtm;
