DROP TABLE IF EXISTS clusteredbuildings;

DO $$
DECLARE
    features_per_cluster FLOAT := current_setting('area_splitter.num_buildings');
    desired_tasks INTEGER := current_setting('area_splitter.num_enumerators');
BEGIN

    IF desired_tasks > 0 THEN
    IF ROUND(features_per_cluster) != 0 THEN
        RAISE EXCEPTION
            'Only one out of buildings and enumerators should be set';
    END IF;
    features_per_cluster =
        (SELECT SUM(numfeatures) FROM splitpolygons) / desired_tasks::float;
    END IF;

-- Calculate a tentative number of tasks per partition.
    DROP TABLE IF EXISTS partition_tasks;
    create table partition_tasks as
        select polyid, numfeatures,
        greatest(1,round(numfeatures/features_per_cluster))::int tasks
        from splitpolygons WHERE numfeatures > 0;

    -- Now adjust the tasks assigned to match the total tasks exactly with the
    -- user-supplied desired number of enumerators.

    -- If enumerators are less than the number of partitions formed by linear features (2),
    -- then we failback to the task merging that is done in the end. Otherwise,
    -- we adjust the per-partition tasks based on the feature density (features per partition)
    -- So, if the actual tasks are more than the desired tasks, we decrement the
    -- number of mappers in the partition that has the least feature density. Similarly if
    -- the actual tasks are less, we increment the mappers in the most feature-dense
    -- partition because those would be the ones with maximum work load. We keep on
    -- doing this until enumerators matches the desired enumerators.
    --
    -- We do this only when area splitting is based on number of enumerators, not for
    -- feature-based area splitting. (1)

    IF desired_tasks > 0 AND -- (1)
       desired_tasks >= (SELECT count(*) from partition_tasks) THEN -- (2)
        DECLARE
            total_tasks BIGINT =
                (SELECT sum(tasks) from partition_tasks);
            tasks_diff INT = ABS(total_tasks - desired_tasks);
        BEGIN
            FOR i IN 1..tasks_diff LOOP
                IF total_tasks > desired_tasks THEN
                    update partition_tasks set tasks = tasks - 1
                    where polyid =
                     (select polyid from partition_tasks where tasks > 1
                      order by numfeatures::float/tasks limit 1);
                ELSE
                    update partition_tasks set tasks = tasks + 1
                    where polyid =
                     (select polyid from partition_tasks
                      order by numfeatures::float/tasks desc limit 1);
                END IF;
            END LOOP;
            IF desired_tasks != (SELECT sum(tasks) from partition_tasks) THEN
                RAISE EXCEPTION 'Desired tasks: %. Created % tasks instead. Aborting...',
                    desired_tasks, (SELECT sum(tasks) from partition_tasks);
            END IF;
        END;
    END IF;

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
                (select tasks::int from partition_tasks
                 where partition_tasks.polyid = buildingstocluster.polyid)
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
END $$;

-- ALTER TABLE clusteredbuildings ADD PRIMARY KEY(osm_id);
SELECT POPULATE_GEOMETRY_COLUMNS('clusteredbuildings'::regclass);
CREATE INDEX clusteredbuildings_idx
ON clusteredbuildings
USING gist (geom);
-- VACUUM ANALYZE clusteredbuildings;
