 /*
Licence: GPLv3 <https://www.gnu.org/licenses/gpl-3.0.html>
Part of the HOT Field Mapping Tasking Manager (FMTM)

Inputs:
- Polygon layer splitpolygons from previous fmtm-split step
- Polygon layer buildings from previous fmtm-split step (contains column with the id of the polygons the buildings are in)

Outputs:
- Polygon layer clusteredbuildings; contains a column clusteruid
*/

/*
***********************PARAMETERS FOR ROB**********************
- Line 46: The desired number of buildings per task (determines cluster size)
*/

DROP TABLE IF EXISTS clusteredbuildings;
CREATE TABLE clusteredbuildings AS (
  WITH splitpolygonswithcontents AS (
    SELECT *
    FROM splitpolygons sp
    WHERE sp.numfeatures > 0
  )
  -- Add the count of features in the splitpolygon each building belongs to
  -- to the buildings table; sets us up to be able to run the clustering.
  ,buildingswithcount AS (
    SELECT b.*, p.numfeatures
    FROM buildings b 
    LEFT JOIN splitpolygons p
    ON b.polyid = p.polyid
  )
  -- Cluster the buildings within each splitpolygon. The second term in the
  -- call to the ST_ClusterKMeans function is the number of clusters to create,
  -- so we're dividing the number of features by a constant (10 in this case)
  -- to get the number of clusters required to get close to the right number
  -- of features per cluster.
  -- TODO: This should certainly not be a hardcoded, the number of features
  --       per cluster should come from a project configuration table
  ,buildingstocluster as (
    SELECT * FROM buildingswithcount bc
    WHERE bc.numfeatures > 0
  )
  ,clusteredbuildingsnocombineduid AS (
  SELECT *,
    ST_ClusterKMeans(geom, cast((b.numfeatures / 20) + 1 as integer))
    over (partition by polyid) as cid
  FROM buildingstocluster b
  )
  -- uid combining the id of the outer splitpolygon and inner cluster
  ,clusteredbuildings as (
    select *, 
    polyid::text || '-' || cid as clusteruid
    from clusteredbuildingsnocombineduid
  )
  SELECT * FROM clusteredbuildings
);  
ALTER TABLE clusteredbuildings ADD PRIMARY KEY(osm_id);
SELECT Populate_Geometry_Columns('public.clusteredbuildings'::regclass);
CREATE INDEX clusteredbuildings_idx
  ON clusteredbuildings
  USING GIST (geom);
VACUUM ANALYZE clusteredbuildings;
