SELECT (ST_Dump(ST_Polygonize(ST_Node(multi_geom)))).geom
FROM   (
  SELECT ST_Collect(geom) AS multi_geom
  FROM   osmlines
) q
;
