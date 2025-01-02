-- ## Migration to create a table to store new and bad geometries.

-- Start a transaction

BEGIN;

CREATE TABLE geometrylog (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY NOT NULL,
    status geomstatus,
    project_id int,
    task_id int
);

ALTER TABLE geometrylog OWNER TO fmtm;

-- Indexes for efficient querying
CREATE INDEX idx_geometrylog ON geometrylog USING gist (geom);

-- Commit the transaction
COMMIT;
