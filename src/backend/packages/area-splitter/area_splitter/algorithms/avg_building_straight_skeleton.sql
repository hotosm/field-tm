/*
 * Running straight skeleton on (the empty space between) all the buildings
 * together is quite slow. So the idea is to reduce the entities on which to
 * run the algorithm. We do this by running it on hulls each containing a
 * cluster of buildings rather than on all the individual buildings. This
 * speeds it up by roughly 7 times.
 *
 * Regardless of whether the hulls are convex or concave, there are chances
 * that they would intersect each other and also with the buildings of the
 * neighbouring cluster's buildings. So first clip the convex hull by its
 * intersections and then merge back any protruding buildings of it own. This
 * will result in a disjoint hull containing its and only its buildings. This
 * hull itself would usually serve as a task polygon and so in most of the
 * cases we would be done with splitting work; just that the task polygons
 * won't share their border which should be fine. But, in some cases there
 * might be one or more buildings that are completely taken out due to the
 * clipping so they are not merged back into the clipped hulls. Hence, we
 * anyway require a straight skeleton algorithm to be run in order to merge
 * back the separated buildings with their original hulls.
 *
 * Now, the final clipped hulls themselves might touch each other if any of the
 * buildings at the border of the hull shares its edge or point with that of a
 * similar building in the adjacent cluster hull. The straight skeleton
 * algorithm inherently fails with touching intersections. Handle this by
 * removing a tiny touching region from both of the hulls.
 */

DROP TABLE IF EXISTS taskpolygons;
create table taskpolygons AS (
  -- explain analyze
  WITH
  /* Generate convex hulls around each cluster. Also store a union of all the
   * buildings in that cluster. This will be needed later to merge back clipped
   * buildings into the clipped hulls.
   */
  convex_hulls as
  (select clusteruid, ST_ConvexHull(ST_Collect(geom)) geom,
           ST_Union(geom) buildings_union
           from clusteredbuildings group by clusteruid
  ),

  /* Get the intersections made by all the hulls with each other.
   *
   * When later we would clip the polygons by their intersections, they would
   * touch each other at the intersection vertices, which CG_StraightSkeleton()
   * does not like. So expand the intersection by a little bit (say, 1% of the
   * hull length) using ST_Buffer().
   *
   * Group the intersections by cluster id.
   */
  intersections_union as
  (select clusteruid, ST_Union(intersection) geom from
    (select c1.clusteruid,
      ST_Buffer(ST_Intersection(c1.geom, c2.geom),
                ST_MaxDistance(c1.geom, c1.geom)/100,
                'endcap=square join=mitre') intersection
      from convex_hulls c1 inner join convex_hulls c2
      on c1.clusteruid != c2.clusteruid and ST_Intersects(c1.geom, c2.geom))
    group by clusteruid
  ),

  /* Clip the convex hulls by their intersections using ST_Difference().
   * The intersections will also include point/line touches if present, but
   * they will be ignored (which is what we want) because ST_Difference() with
   * a polygon and a point/line returns the same polygon.
   *
   * The clipped hull may have lost buildings at its border either partially or
   * entirely. Merge back these clipped buildings into the hull area by doing
   * an ST_Union() with the entire buildings_union that we saved earlier. Note:
   * The resultant union will be a MULTIPOLYGON if some clipped buildings were
   * entirely outside of the hull (which is rare but possible)
   */
  clipped_hulls as
  (select
      h.clusteruid,
      -- Also include disjoint hulls as-is
      case
        when iu.geom is null then h.geom
        else ST_Union(ST_Difference(h.geom, iu.geom), h.buildings_union) end geom
     from convex_hulls h left outer join intersections_union iu
     on h.clusteruid = iu.clusteruid
  ),

  -- As mentioned, some can have multipolygons. Separate them by ST_Dump().
  final_hulls as
  (select clusteruid, (ST_Dump(geom)).geom from clipped_hulls
  ),

/* Now, the final clipped hulls themselves might touch each other if any of the
 * buildings at the border of a hull shares its edge or point with that in the
 * adjacent cluster hull. The straight skeleton algorithm inherently fails with
 * touching intersections. Handle this by removing a tiny area from both of the
 * hulls that covers this touching point/line. So do the clipping again here
 * similar to above, but this time with final_hulls.
 */

 /* First, collect the touching regions. */
  touching_regions as
  (select clusteruid, ST_Union(intersection) geom from
    (select c1.clusteruid,
      ST_Buffer(ST_Intersection(c1.geom, c2.geom),
                0.0000005, 'endcap=square join=mitre') intersection
      from final_hulls c1 inner join final_hulls c2
      on c1.clusteruid != c2.clusteruid and ST_Intersects(c1.geom, c2.geom))
    group by clusteruid
  ),

  /* Then, clip the hulls with the touching regions. */
  final_hulls_untouched as
  (select
      h.clusteruid,
      -- Include the non-touching hulls as-is
      case when iu.geom is null then h.geom
           else ST_Difference(h.geom, iu.geom)
      end geom
     from final_hulls h left outer join touching_regions iu
     on h.clusteruid = iu.clusteruid
  ),

  -- Get the empty space between buildings.
  aoi_minus_hulls as
  (select ST_Difference(
          (select geom from project_aoi), -- Assume there's a single AOI
          ST_Union(array(select geom from final_hulls_untouched))) geom
  ),


/* Generate the straight skeleton lines on this empty space.  Most of these
 * skeleton lines form closed polygons, except the lines emerging from the
 * hulls' vertices. We anyway don't want these lines. Build a table of all
 * these polygons. Each of these polygons contain one and only one hull. And
 * each hull is guaranteed to be within a polygon. So there is a one-to-one
 * mapping between the hulls and the skeleton polygons.
 *
 * Also include the AOI perimeter lines. These help form polygons around hulls
 * that cross the AOI perimeter. Without this, the skeleton lines would not
 * complete the polygons around such hulls, effectively excluding the
 * corresponding clusters.
 *
 * The ST_UnaryUnion() 2nd argument (grid size) is there to blend line segments
 * that do not form a complete link or overlap a bit at the vertices. Otherwise
 * ST_Polygonize() fails to form polygons out of such lines.
 */
-- create table skeleton_lines as select CG_StraightSkeleton(geom) geom from aoi_minus_hulls;
  skeleton_polygons as
  (select (ST_Dump(ST_Polygonize(ST_UnaryUnion(geom, 0.0000001)))).geom
    from (select ST_Union(CG_StraightSkeleton(geom),
                          (select ST_Boundary(geom) from project_aoi))  geom
          from aoi_minus_hulls)
  ),

/* Associate each of these polygons to the clusterid of the convex hull
 * within that polygon.
 *
 * We could have used ST_Within() for this, but there are subtle corner cases
 * where portions of hulls cross the polygon boundary. This happens
 * specifically because the lines generated by straight skeleton are
 * grid-snapped (See ST_UnaryUnion above) before making the polygons, so they
 * don't precisely coincide with the polygon edges; and at the regions where
 * the hulls touch each other this may lead to hulls crossing the task polygon
 * boundary slightly. So just check whether the hull centroid is within the
 * polygon.
 */
  skeleton_clusters as
  (select f.clusteruid, s.geom from skeleton_polygons s, final_hulls_untouched f
    where ST_Intersects(ST_Centroid(f.geom), s.geom)
  )

/* As mentioned above, there can be some buildings that were completely clipped
 * out of the convex hulls. For each of such buildings, the straight skeleton
 * forms a polygon around it. Merge all such polygons into the adjacent
 * hull belonging to the same cluster, to form one single polygon associated
 * with a common cluster id. Each such polygon now represents a task.
 */

  select ST_UNION(geom) geom, ROW_NUMBER() OVER () AS taskid
    from skeleton_clusters GROUP BY clusteruid
);

-- /* For testing:
 DROP TABLE IF EXISTS my_taskpolygons;
 create table my_taskpolygons AS select * from taskpolygons;
 -- */
