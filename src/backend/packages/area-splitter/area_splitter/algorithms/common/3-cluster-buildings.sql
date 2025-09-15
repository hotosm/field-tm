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
