-- Build as index on the taskpolygons
ALTER TABLE taskpolygons ADD PRIMARY KEY (taskid);
SELECT POPULATE_GEOMETRY_COLUMNS('taskpolygons'::regclass);
CREATE INDEX taskpolygons_idx
ON taskpolygons
USING gist (geom);

-- Internal splitlines (rivers/roads/etc. from step 1), i.e. the boundaries
-- introduced by linear features but not the outer AOI edge. Used below to
-- reject neighbour merges whose shared boundary lies along a splitline -
-- otherwise the small-polygon merge can re-fuse polygons across a river
-- that the earlier stages deliberately separated. Empty geometry when the
-- AOI has no intersecting linear features, in which case the filter is a
-- no-op.
DROP TABLE IF EXISTS pg_temp.splitline_union;
CREATE TEMP TABLE splitline_union AS
    SELECT COALESCE(
        ST_Difference(
            (SELECT ST_Union(ST_Boundary(geom)) FROM splitpolygons),
            (SELECT ST_Boundary(geom) FROM project_aoi)
        ),
        'GEOMETRYCOLLECTION EMPTY'::geometry
    ) AS geom;

-- Merge least feature polygons with neighbouring polygons
DO $$
DECLARE
    num_buildings INTEGER := current_setting('area_splitter.num_buildings');
    num_enumerators INTEGER := current_setting('area_splitter.num_enumerators');
    min_area NUMERIC; -- Set the minimum area threshold
    mean_area NUMERIC;
    stddev_area NUMERIC; -- Set the standard deviation
    min_buildings INTEGER; -- Set the minimum number of buildings threshold
    small_polygon RECORD; -- set small_polygon and nearest_neighbor as record 
    nearest_neighbor RECORD; -- in order to use them in the loop
    merges_remaining INTEGER = NULL;
BEGIN

    DROP TABLE IF EXISTS pg_temp.leastfeaturepolygons;
    IF num_enumerators > 0 THEN
      merges_remaining = (SELECT COUNT(*) FROM taskpolygons) - num_enumerators;
      IF merges_remaining < 0 THEN
        merges_remaining = 0; -- Skip merging
      END IF;
      CREATE TEMP TABLE leastfeaturepolygons AS
        SELECT taskid, geom,
        (SELECT COUNT(b.id) FROM buildings b
          WHERE ST_Intersects(taskpolygons.geom, b.geom)) numbuildings
        FROM taskpolygons ORDER BY numbuildings ASC LIMIT merges_remaining;
    ELSE
      -- Find the mean and standard deviation of the area
      SELECT
          AVG(ST_Area(geom)),
          STDDEV_POP(ST_Area(geom))
      INTO mean_area, stddev_area
      FROM taskpolygons;

      -- Set the threshold as mean - standard deviation
      min_area := mean_area - stddev_area;
      min_buildings := num_buildings * 0.5;

      CREATE TEMP TABLE leastfeaturepolygons AS
      SELECT taskid, geom
      FROM taskpolygons
      WHERE ST_Area(geom) < min_area OR
        (
          SELECT COUNT(b.id) FROM buildings b
          WHERE ST_Contains(taskpolygons.geom, b.geom)
        ) < min_buildings; -- find least feature polygons based on the area and feature

    END IF;

    FOR small_polygon IN
        SELECT * FROM leastfeaturepolygons
    LOOP
        -- If the required # of polygons are merged, we are done.
        IF merges_remaining = 0 THEN
          EXIT;
        END IF;

        -- Per-polygon block so a GEOS TopologyException on one neighbour
        -- pair skips this small polygon (leaves it unmerged) instead of
        -- aborting the entire alignment step.
        BEGIN
            -- Find the nearest neighbor to merge the small polygon with.
            --
            -- ST_Intersection uses a fixed precision grid (3rd arg, ~1 mm
            -- at the equator) to avoid GEOS "side location conflict"
            -- topology exceptions from sub-precision degeneracies in the
            -- Voronoi + clip output. ST_MakeValid repairs any remaining
            -- micro-invalidities (e.g. ring self-touches) before the
            -- operation. Both are cheap per call; the inner SELECT is
            -- already gated by ST_Touches + the gist index so only a few
            -- candidate neighbours are scanned per small polygon.
            FOR nearest_neighbor IN
            WITH candidates AS (
                SELECT taskid, geom,
                    ST_Intersection(
                        ST_MakeValid(small_polygon.geom),
                        ST_MakeValid(geom),
                        0.00000001
                    ) AS shared_geom
                FROM taskpolygons
                WHERE taskid NOT IN (SELECT taskid FROM leastfeaturepolygons)
                AND ST_Touches(small_polygon.geom, geom)
            )
            SELECT c.taskid, c.geom,
                ST_LENGTH2D(c.shared_geom) AS shared_bound
            FROM candidates c, splitline_union s
            WHERE ST_GEOMETRYTYPE(c.shared_geom) != 'ST_Point'
              -- Reject if the shared boundary lies mostly on a splitline;
              -- merging across a river/road would erase the intended
              -- partition. 0.5 is a heuristic - a small polygon touching
              -- a neighbour half-along a river is more river-crossing
              -- than genuine adjacency.
              AND (
                ST_LENGTH2D(c.shared_geom) = 0
                OR ST_LENGTH2D(ST_Intersection(c.shared_geom, s.geom))
                     / ST_LENGTH2D(c.shared_geom) < 0.5
              )
            ORDER BY shared_bound DESC  -- Find neighbor polygon based on shared boundary distance
            LIMIT 1
            LOOP
                -- Merge the small polygon into the neighboring polygon
                UPDATE taskpolygons
                SET geom = ST_MakeValid(ST_Union(geom, small_polygon.geom))
                WHERE taskid = nearest_neighbor.taskid;

                DELETE FROM taskpolygons WHERE taskid = small_polygon.taskid;

                IF merges_remaining IS NOT NULL THEN -- Fixed number of mappers
                  merges_remaining = merges_remaining - 1;
                END IF;

                -- Exit the neighboring polygon loop after one successful merge
                EXIT;
            END LOOP;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Skipping merge for taskid % due to geometry error: %',
                small_polygon.taskid, SQLERRM;
        END;
    END LOOP;
END $$;

DROP TABLE IF EXISTS pg_temp.leastfeaturepolygons;
DROP TABLE IF EXISTS pg_temp.splitline_union;
-- VACUUM ANALYZE taskpolygons;
