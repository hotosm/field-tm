CREATE TYPE fieldmappingapp AS ENUM ('QField', 'ODK', 'FieldTM');
ALTER TYPE fieldmappingapp OWNER TO CURRENT_USER;

CREATE TYPE projectstatus AS ENUM (
    'ARCHIVED',
    'PUBLISHED',
    'DRAFT',
    'COMPLETED'
);
ALTER TYPE projectstatus OWNER TO CURRENT_USER;

CREATE TYPE projectvisibility AS ENUM (
    'PUBLIC',
    'PRIVATE'
);
ALTER TYPE projectvisibility OWNER TO CURRENT_USER;

CREATE TYPE projectrole AS ENUM (
    'MAPPER',
    'PROJECT_MANAGER'
);
ALTER TYPE projectrole OWNER TO CURRENT_USER;
