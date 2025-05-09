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
