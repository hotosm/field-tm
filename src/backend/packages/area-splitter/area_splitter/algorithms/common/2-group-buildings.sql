DROP TABLE IF EXISTS buildings;
CREATE TABLE buildings AS (
    SELECT
        b.*,
        polys.polyid
    FROM ways_poly AS b, polygonsnocount AS polys
    WHERE
        ST_INTERSECTS(polys.geom, ST_CENTROID(b.geom))
        AND b.tags ->> 'building' IS NOT NULL
);


-- ALTER TABLE buildings ADD PRIMARY KEY(osm_id);


-- Properly register geometry column (makes QGIS happy)
SELECT POPULATE_GEOMETRY_COLUMNS('public.buildings'::regclass);
-- Add a spatial index (vastly improves performance for a lot of operations)
CREATE INDEX buildings_idx
ON buildings
USING gist (geom);
-- Clean up the table which may have gaps and stuff from spatial indexing
-- VACUUM ANALYZE buildings;

DROP TABLE IF EXISTS splitpolygons;
CREATE TABLE splitpolygons AS (
    WITH polygonsfeaturecount AS (
        SELECT
            sp.polyid,
            sp.geom,
            sp.geog,
            COUNT(b.geom) AS numfeatures,
            ST_AREA(sp.geog) AS area
        FROM polygonsnocount AS sp
        LEFT JOIN buildings AS b
            ON sp.polyid = b.polyid
        GROUP BY sp.polyid, sp.geom
    )

    SELECT * FROM polygonsfeaturecount
);
ALTER TABLE splitpolygons ADD PRIMARY KEY (polyid);
SELECT POPULATE_GEOMETRY_COLUMNS('public.splitpolygons'::regclass);
CREATE INDEX splitpolygons_idx
ON splitpolygons
USING gist (geom);
-- VACUUM ANALYZE splitpolygons;

DROP TABLE polygonsnocount;

-- DROP TABLE IF EXISTS lowfeaturecountpolygons;
-- CREATE TABLE lowfeaturecountpolygons AS (
-- -- Grab the polygons with fewer than the requisite number of features
--     WITH lowfeaturecountpolys AS (
--         SELECT *
--         FROM splitpolygons AS p
--         -- TODO: feature count should not be hard-coded
--         WHERE p.numfeatures < %(num_buildings)s
--     ),

--     -- Find the neighbors of the low-feature-count polygons
--     -- Store their ids as n_polyid, numfeatures as n_numfeatures, etc
--     allneighborlist AS (
--         SELECT
--             p.*,
--             pf.polyid AS n_polyid,
--             pf.area AS n_area,
--             p.numfeatures AS n_numfeatures,
--             -- length of shared boundary to make nice merge decisions 
--             ST_LENGTH2D(ST_INTERSECTION(p.geom, pf.geom)) AS sharedbound
--         FROM lowfeaturecountpolys AS p
--         INNER JOIN splitpolygons AS pf
--             -- Anything that touches
--             ON ST_TOUCHES(p.geom, pf.geom)
--             -- But eliminate those whose intersection is a point, because
--             -- polygons that only touch at a corner shouldn't be merged
--             AND ST_GEOMETRYTYPE(ST_INTERSECTION(p.geom, pf.geom)) != 'ST_Point'
--         -- Sort first by polyid of the low-feature-count polygons
--         -- Then by descending featurecount and area of the 
--         -- high-feature-count neighbors (area is in case of equal 
--         -- featurecounts, we'll just pick the biggest to add to)
--         ORDER BY p.polyid ASC, p.numfeatures DESC, pf.area DESC
--     -- OR, maybe for more aesthetic merges:
--     -- order by p.polyid, sharedbound desc
--     )

--     SELECT DISTINCT ON (a.polyid) * FROM allneighborlist AS a
-- );
-- ALTER TABLE lowfeaturecountpolygons ADD PRIMARY KEY (polyid);
-- SELECT POPULATE_GEOMETRY_COLUMNS('public.lowfeaturecountpolygons'::regclass);
-- CREATE INDEX lowfeaturecountpolygons_idx
-- ON lowfeaturecountpolygons
-- USING gist (geom);
-- VACUUM ANALYZE lowfeaturecountpolygons;
