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
    pair RECORD;
    gap RECORD;
    merged BOOLEAN;
BEGIN

    DROP TABLE IF EXISTS pg_temp.leastfeaturepolygons;
    IF num_enumerators > 0 THEN
      -- Fixed number of tasks: merge the task with the fewest buildings into
      -- a neighbour until the count matches. Merges across a splitline only
      -- happen once no other merge is possible (more partitions than
      -- enumerators). Islands with no neighbour are left as they are.

      -- First give uncovered parts of the AOI (e.g. partitions without
      -- buildings, which the skeleton leaves out) to the neighbouring task
      -- with the longest shared edge, so tasks around them can merge.
      FOR gap IN
        SELECT (ST_Dump(ST_CollectionExtract(
          ST_Difference(a.geom, ST_Union(t.geom), 0.00000001), 3))).geom AS geom
        FROM project_aoi a, taskpolygons t GROUP BY a.geom
      LOOP
        BEGIN
          UPDATE taskpolygons SET geom = ST_MakeValid(ST_Union(geom, gap.geom))
          WHERE taskid = (
            SELECT t.taskid FROM taskpolygons t
            WHERE t.geom && gap.geom AND ST_Intersects(t.geom, gap.geom)
            ORDER BY ST_Length(ST_CollectionExtract(
              ST_Intersection(t.geom, gap.geom, 0.00000001), 2)) DESC
            LIMIT 1
          );
        EXCEPTION WHEN OTHERS THEN
          RAISE NOTICE 'Skipping uncovered area: %', SQLERRM;
        END;
      END LOOP;

      DROP TABLE IF EXISTS pg_temp.taskcounts;
      CREATE TEMP TABLE taskcounts AS
        SELECT t.taskid,
          (SELECT COUNT(*) FROM buildings b
            WHERE ST_Contains(t.geom, ST_PointOnSurface(b.geom))) AS n
        FROM taskpolygons t;
      DROP TABLE IF EXISTS pg_temp.splitline_buffer;
      CREATE TEMP TABLE splitline_buffer AS
        SELECT ST_SetSRID(ST_Buffer(geom, 0.0000001), 4326) AS geom FROM splitline_union;

      WHILE (SELECT COUNT(*) FROM taskpolygons) > num_enumerators LOOP
        merged := FALSE;
        FOR pair IN
          WITH pairs AS (
            SELECT s.taskid AS small_id, n.taskid AS nb_id, sc.n,
              ST_CollectionExtract(
                ST_Intersection(ST_MakeValid(s.geom), ST_MakeValid(n.geom), 0.00000001), 2
              ) AS shared
            FROM taskpolygons s
            JOIN taskcounts sc ON sc.taskid = s.taskid
            JOIN taskpolygons n ON n.taskid != s.taskid AND s.geom && n.geom
              AND ST_Intersects(s.geom, n.geom)
          ),
          scored AS (
            SELECT small_id, nb_id, n,
              ST_Length(shared) AS shared_len,
              ST_Length(ST_Intersection(shared, b.geom)) AS on_splitline
            FROM pairs, splitline_buffer b
          )
          SELECT small_id, nb_id FROM scored
          WHERE shared_len > 0
          ORDER BY (on_splitline / shared_len >= 0.5), n, shared_len DESC
        LOOP
          BEGIN
            UPDATE taskpolygons
            SET geom = ST_MakeValid(ST_Union(geom,
              (SELECT geom FROM taskpolygons WHERE taskid = pair.small_id)))
            WHERE taskid = pair.nb_id;
            DELETE FROM taskpolygons WHERE taskid = pair.small_id;
            UPDATE taskcounts SET n = n + (SELECT n FROM taskcounts WHERE taskid = pair.small_id)
            WHERE taskid = pair.nb_id;
            DELETE FROM taskcounts WHERE taskid = pair.small_id;
            merged := TRUE;
            EXIT;
          EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Skipping merge of task % into %: %',
              pair.small_id, pair.nb_id, SQLERRM;
          END;
        END LOOP;
        EXIT WHEN NOT merged;
      END LOOP;

      DROP TABLE IF EXISTS pg_temp.taskcounts;
      DROP TABLE IF EXISTS pg_temp.splitline_buffer;
      RETURN;
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
