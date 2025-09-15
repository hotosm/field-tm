DROP TABLE IF EXISTS polygonsnocount;
-- Create a new polygon layer of splits by lines

DO $$
    DECLARE 
    lines_count INTEGER;
BEGIN
    -- Check if ways_line has any data
    SELECT COUNT(*) INTO lines_count
    FROM "ways_line" l
    WHERE (
        (l.tags->>'highway' IS NOT NULL AND 
        l.tags->>'highway' NOT IN ('unclassified', 'residential', 'service', 'pedestrian', 'track', 'bus_guideway'))
        OR l.tags->>'waterway' IS NOT NULL
        OR l.tags->>'railway' IS NOT NULL
    );
    IF lines_count > 0 THEN
    CREATE TABLE polygonsnocount AS (
        -- The Area of Interest provided by the person creating the project
        WITH aoi AS (
            SELECT * FROM "project_aoi"
        )
        -- Extract all lines to be used as splitlines from a table of lines
        -- with the schema from Underpass (all tags as jsonb column called 'tags')
        -- TODO: add polygons (closed ways in OSM) with a 'highway' tag;
        -- some features such as roundabouts appear as polygons.
        -- TODO: add waterway polygons; now a beach doesn't show up as a splitline.
        -- TODO: these tags should come from another table rather than hardcoded
        -- so that they're easily configured during project creation.
        , splitlines AS (
            SELECT ST_Intersection(a.geom, l.geom) AS geom
            FROM aoi a
            JOIN "ways_line" l ON ST_Intersects(a.geom, l.geom)
            WHERE (
                (l.tags->>'highway' IS NOT NULL AND 
                l.tags->>'highway' NOT IN ('unclassified', 'residential', 'service', 'pedestrian', 'track', 'bus_guideway')) -- TODO: update(add/remove) this based on the requirements later
                OR l.tags->>'waterway' IS NOT NULL
                OR l.tags->>'railway' IS NOT NULL
            )
        )
            
        --     SELECT * from lines_view l
        --    WHERE (
        --         (l.tags->>'highway' IS NOT NULL AND 
        --         l.tags->>'highway' NOT IN ('unclassified', 'residential', 'service', 'pedestrian', 'track', 'bus_guideway'))
        --         OR l.tags->>'waterway' IS NOT NULL
        --         OR l.tags->>'railway' IS NOT NULL
        --     )
        -- )
        -- Merge all lines, necessary so that the polygonize function works later
        ,merged AS (
            SELECT ST_LineMerge(ST_Union(splitlines.geom)) AS geom
            FROM splitlines
        )
        -- Combine the boundary of the AOI with the splitlines
        -- First extract the Area of Interest boundary as a line
        ,boundary AS (
            SELECT ST_Boundary(geom) AS geom
            FROM aoi
        )
        -- Then combine it with the splitlines
        ,comb AS (
            SELECT ST_Union(boundary.geom, merged.geom) AS geom
            FROM boundary, merged
        )
        -- TODO add closed ways from OSM to lines (roundabouts etc)
        -- Create a polygon for each area enclosed by the splitlines
        ,splitpolysnoindex AS (
            SELECT (ST_Dump(ST_Polygonize(comb.geom))).geom as geom
            FROM comb
        )
        -- Add an index column to the split polygons
        ,splitpolygons AS(
            SELECT
            row_number () over () as polyid,
                ST_Transform(spni.geom,4326)::geography AS geog,
            spni.* 
            from splitpolysnoindex spni
        )
        SELECT * FROM splitpolygons
    );
    ELSE
        -- Calculate number of buildings per cluster
        CREATE TABLE polygonsnocount AS (
            WITH aoi AS (
                SELECT * FROM "project_aoi"
            )
            ,transformed_aoi AS(
                SELECT
                row_number () over () as polyid,
                ST_Transform(aoi.geom,4326)::geography AS geog,
                aoi.geom 
                from aoi
            )
            SELECT * FROM transformed_aoi
        );
    END IF;
END $$;


-- Make that index column a primary key
ALTER TABLE polygonsnocount ADD PRIMARY KEY (polyid);
-- Properly register geometry column (makes QGIS happy)
SELECT POPULATE_GEOMETRY_COLUMNS('public.polygonsnocount'::regclass);
-- Add a spatial index (vastly improves performance for a lot of operations)
CREATE INDEX polygonsnocount_idx
ON polygonsnocount
USING gist (geom);
-- Clean up the table which may have gaps and stuff from spatial indexing
-- VACUUM ANALYZE polygonsnocount;


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


DROP TABLE IF EXISTS clusteredbuildings;
CREATE TABLE clusteredbuildings AS (
    WITH splitpolygonswithcontents AS (
        SELECT *
        FROM splitpolygons
        WHERE numfeatures > 0
    ),

    -- Add the count of features in the splitpolygon each building belongs to
    -- to the buildings table; sets us up to be able to run the clustering.
    buildingswithcount AS (
        SELECT
            b.*,
            sp.numfeatures
        FROM buildings AS b
        LEFT JOIN splitpolygonswithcontents AS sp
            ON b.polyid = sp.polyid
    ),

    -- Cluster the buildings within each splitpolygon. The second term in the
    -- call to the ST_ClusterKMeans function is the number of clusters to 
    -- create, so we're dividing the number of features by a constant 
    -- (10 in this case) to get the number of clusters required to get close
    -- to the right number of features per cluster.
    -- TODO: This should certainly not be a hardcoded, the number of features
    --       per cluster should come from a project configuration table
    buildingstocluster AS (
        SELECT * FROM buildingswithcount
        WHERE numfeatures > 0
    ),

    clusteredbuildingsnocombineduid AS (
        SELECT
            *,
            ST_CLUSTERKMEANS(
                geom,
                CAST((numfeatures / %(num_buildings)s) + 1 AS integer)
            )
                OVER (PARTITION BY polyid)
            AS cid
        FROM buildingstocluster
    ),

    -- uid combining the id of the outer splitpolygon and inner cluster
    clusteredbuildings AS (
        SELECT
            *,
            polyid::text || '-' || cid AS clusteruid
        FROM clusteredbuildingsnocombineduid
    )

    SELECT * FROM clusteredbuildings
);
-- ALTER TABLE clusteredbuildings ADD PRIMARY KEY(osm_id);
SELECT POPULATE_GEOMETRY_COLUMNS('public.clusteredbuildings'::regclass);
CREATE INDEX clusteredbuildings_idx
ON clusteredbuildings
USING gist (geom);
-- VACUUM ANALYZE clusteredbuildings;


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

-- Merge least feature polygons with neighbouring polygons
DO $$
DECLARE
    num_buildings INTEGER := %(num_buildings)s;
    min_area NUMERIC; -- Set the minimum area threshold
    mean_area NUMERIC;
    stddev_area NUMERIC; -- Set the standard deviation
    min_buildings INTEGER; -- Set the minimum number of buildings threshold
    small_polygon RECORD; -- set small_polygon and nearest_neighbor as record 
    nearest_neighbor RECORD; -- in order to use them in the loop
BEGIN
    min_buildings := num_buildings * 0.5;

    -- Find the mean and standard deviation of the area
    SELECT 
        AVG(ST_Area(geom)),
        STDDEV_POP(ST_Area(geom))
    INTO mean_area, stddev_area
    FROM taskpolygons;

    -- Set the threshold as mean - standard deviation
    min_area := mean_area - stddev_area;

    DROP TABLE IF EXISTS leastfeaturepolygons;
    CREATE TABLE leastfeaturepolygons AS
    SELECT taskid, geom
    FROM taskpolygons
    WHERE ST_Area(geom) < min_area OR (
        SELECT COUNT(b.id) FROM buildings b 
        WHERE ST_Contains(taskpolygons.geom, b.geom)
    ) < min_buildings; -- find least feature polygons based on the area and feature

    FOR small_polygon IN 
        SELECT * FROM leastfeaturepolygons
    LOOP
        -- Find the nearest neighbor to merge the small polygon with
        FOR nearest_neighbor IN
        SELECT taskid, geom, ST_LENGTH2D(ST_Intersection(small_polygon.geom, geom)) as shared_bound
        FROM taskpolygons
        WHERE taskid NOT IN (SELECT taskid FROM leastfeaturepolygons)
        AND ST_Touches(small_polygon.geom, geom)
        AND ST_GEOMETRYTYPE(ST_INTERSECTION(small_polygon.geom, geom)) != 'ST_Point'
        ORDER BY shared_bound DESC  -- Find neighbor polygon based on shared boundary distance
        LIMIT 1
        LOOP
            -- Merge the small polygon into the neighboring polygon
            UPDATE taskpolygons
            SET geom = ST_Union(geom, small_polygon.geom)
            WHERE taskid = nearest_neighbor.taskid;

            DELETE FROM taskpolygons WHERE taskid = small_polygon.taskid;
            -- Exit the neighboring polygon loop after one successful merge
            EXIT;
        END LOOP;
    END LOOP;
END $$;

DROP TABLE IF EXISTS leastfeaturepolygons;
-- VACUUM ANALYZE taskpolygons;

-- Generate GeoJSON output
SELECT
    JSONB_BUILD_OBJECT(
        'type', 'FeatureCollection',
        'features', JSONB_AGG(feature)
    )
FROM (
    SELECT
        JSONB_BUILD_OBJECT(
            'type', 'Feature',
            'geometry', ST_ASGEOJSON(t.geom)::jsonb,
            'properties', JSONB_BUILD_OBJECT(
                'building_count', (
                    SELECT COUNT(b.id)
                    FROM buildings AS b
                    WHERE ST_CONTAINS(t.geom, b.geom)
                )
            )
        ) AS feature
    FROM taskpolygons AS t
) AS features;
