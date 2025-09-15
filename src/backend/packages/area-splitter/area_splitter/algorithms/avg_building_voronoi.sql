DROP TABLE IF EXISTS dumpedpoints;
CREATE TABLE dumpedpoints AS (
    SELECT
        cb.osm_id,
        cb.polyid,
        cb.cid,
        cb.clusteruid,
        -- POSSIBLE BUG: PostGIS' Voronoi implementation seems to panic
        -- with segments less than 0.00004 degrees.
        -- Should probably use geography instead of geometry
        (ST_DUMPPOINTS(ST_SEGMENTIZE(cb.geom, 0.00004))).geom AS geom
    FROM clusteredbuildings AS cb
);
SELECT POPULATE_GEOMETRY_COLUMNS('public.dumpedpoints'::regclass);
CREATE INDEX dumpedpoints_idx
ON dumpedpoints
USING gist (geom);
-- VACUUM ANALYZE dumpedpoints;

DROP TABLE IF EXISTS voronoids;
CREATE TABLE voronoids AS (
    SELECT
        ST_INTERSECTION((ST_DUMP(ST_VORONOIPOLYGONS(
            ST_COLLECT(points.geom)
        ))).geom,
        sp.geom) AS geom
    FROM dumpedpoints AS points,
        splitpolygons AS sp
    WHERE ST_CONTAINS(sp.geom, points.geom)
    GROUP BY sp.geom
);
CREATE INDEX voronoids_idx
ON voronoids
USING gist (geom);
-- VACUUM ANALYZE voronoids;

DROP TABLE IF EXISTS voronois;
CREATE TABLE voronois AS (
    SELECT
        p.clusteruid,
        v.geom
    FROM voronoids AS v, dumpedpoints AS p
    WHERE ST_WITHIN(p.geom, v.geom)
);
CREATE INDEX voronois_idx
ON voronois
USING gist (geom);
-- VACUUM ANALYZE voronois;
DROP TABLE voronoids;

DROP TABLE IF EXISTS unsimplifiedtaskpolygons;
CREATE TABLE unsimplifiedtaskpolygons AS (
    SELECT
        clusteruid,
        ST_UNION(geom) AS geom
    FROM voronois
    GROUP BY clusteruid
);

CREATE INDEX unsimplifiedtaskpolygons_idx
ON unsimplifiedtaskpolygons
USING gist (geom);

--VACUUM ANALYZE unsimplifiedtaskpolygons;
