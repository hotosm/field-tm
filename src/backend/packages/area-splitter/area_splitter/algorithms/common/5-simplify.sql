--*****************************Simplify*******************************
-- Extract unique line segments
DROP TABLE IF EXISTS taskpolygons;
CREATE TABLE taskpolygons AS (
    --Convert task polygon boundaries to linestrings
    WITH rawlines AS (
        SELECT
            utp.clusteruid,
            ST_BOUNDARY(utp.geom) AS geom
        FROM unsimplifiedtaskpolygons AS utp
    ),

    -- Union, which eliminates duplicates from adjacent polygon boundaries
    unionlines AS (
        SELECT ST_UNION(l.geom) AS geom FROM rawlines AS l
    ),

    -- Dump, which gives unique segments.
    segments AS (
        SELECT (ST_DUMP(l.geom)).geom AS geom
        FROM unionlines AS l
    ),

    agglomerated AS (
        SELECT ST_LINEMERGE(ST_UNARYUNION(ST_COLLECT(s.geom))) AS geom
        FROM segments AS s
    ),

    simplifiedlines AS (
        SELECT ST_SIMPLIFY(a.geom, 0.000075) AS geom
        FROM agglomerated AS a
    ),

    taskpolygonsnoindex AS (
        SELECT (ST_DUMP(ST_POLYGONIZE(s.geom))).geom AS geom
        FROM simplifiedlines AS s
    )

    SELECT
        tpni.*,
        ROW_NUMBER() OVER () AS taskid
    FROM taskpolygonsnoindex AS tpni
);

ALTER TABLE taskpolygons ADD PRIMARY KEY (taskid);
SELECT POPULATE_GEOMETRY_COLUMNS('public.taskpolygons'::regclass);
CREATE INDEX taskpolygons_idx
ON taskpolygons
USING gist (geom);
