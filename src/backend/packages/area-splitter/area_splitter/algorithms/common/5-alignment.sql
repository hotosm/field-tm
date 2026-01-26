-- Build as index on the taskpolygons
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
