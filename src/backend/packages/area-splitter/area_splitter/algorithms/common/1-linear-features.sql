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
        (
            %(include_roads)s
            AND l.tags->>'highway' IS NOT NULL
            AND l.tags->>'highway' NOT IN ('unclassified', 'residential', 'service', 'pedestrian', 'track', 'bus_guideway')
        )
        OR (
            %(include_rivers)s
            AND l.tags->>'waterway' IS NOT NULL
        )
        OR (
            %(include_railways)s
            AND l.tags->>'railway' IS NOT NULL
        )
        OR (
            %(include_aeroways)s
            AND l.tags->>'aeroway' IS NOT NULL
        )
        OR l.tags->>'barrier' IN ('fence','wire_fence','wall','city_wall','ditch')
        OR l.tags->>'natural' IN ('cliff')
        OR l.tags->>'man_made' IN ('embankment','dyke','dike')
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
                (
                    %(include_roads)s
                    AND l.tags->>'highway' IS NOT NULL
                    AND l.tags->>'highway' NOT IN ('unclassified', 'residential', 'service', 'pedestrian', 'track', 'bus_guideway')
                ) -- TODO: update(add/remove) this based on the requirements later
                OR (
                    %(include_rivers)s
                    AND l.tags->>'waterway' IS NOT NULL
                )
                OR (
                    %(include_railways)s
                    AND l.tags->>'railway' IS NOT NULL
                )
                OR (
                    %(include_aeroways)s
                    AND l.tags->>'aeroway' IS NOT NULL
                )
                OR l.tags->>'barrier' IN ('fence','wire_fence','wall','city_wall','ditch')
                OR l.tags->>'natural' IN ('cliff')
                OR l.tags->>'man_made' IN ('embankment','dyke','dike')
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
        -- Calculate number of building polygons per cluster
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
