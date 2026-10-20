// Splitting SQL shared with the backend area-splitter package (not copied).
import linearFeatures from "@algorithms/common/1-linear-features.sql?raw";
import groupBuildings from "@algorithms/common/2-group-buildings.sql?raw";
import clusterBuildings from "@algorithms/common/3-cluster-buildings.sql?raw";
import alignment from "@algorithms/common/5-alignment.sql?raw";
import extract from "@algorithms/common/6-extract.sql?raw";
import voronoi from "@algorithms/avg_building_voronoi.sql?raw";
import skeleton from "@algorithms/avg_building_straight_skeleton.sql?raw";
import splitByRoads from "@algorithms/split_by_roads.sql?raw";

// PGlite's GEOS can corrupt the engine on this union of task boundaries
// (e.g. buildings plus Overpass roads); a 1e-9 degree grid size avoids it.
export const VORONOI_UNION_ANCHOR = "SELECT ST_UNION(l.geom) AS geom FROM rawlines AS l";

function voronoiSql(original: string) {
  if (!original.includes(VORONOI_UNION_ANCHOR))
    throw new Error(`Voronoi SQL changed: missing "${VORONOI_UNION_ANCHOR}"`);
  return original.replace(
    VORONOI_UNION_ANCHOR,
    "SELECT ST_UNION(l.geom, 1e-9) AS geom FROM rawlines AS l",
  );
}

export const SQL_FILES = {
  SPLIT_BY_ROADS: [linearFeatures, splitByRoads],
  AVG_BUILDING_VORONOI: [
    linearFeatures,
    groupBuildings,
    clusterBuildings,
    voronoiSql(voronoi),
    alignment,
    extract,
  ],
} as const;

// The skeleton SQL calls CG_StraightSkeleton (SFCGAL, not in PGlite). Run it in
// two passes: SKELETON_INPUT stops after the aoi_minus_hulls CTE; JS computes
// the skeleton into planner_skeleton_lines; SKELETON_TASKS reads that instead.
export const SKELETON_ANCHORS = {
  create: "create TEMP table taskpolygons AS (",
  cteEnd: "\n  skeleton_polygons as",
  call: "ST_Union(CG_StraightSkeleton(geom),",
  clip: "ST_Union(ST_Difference(h.geom, iu.geom), h.buildings_union)",
} as const;

function skeletonSql(original: string) {
  for (const a of Object.values(SKELETON_ANCHORS))
    if (!original.includes(a)) throw new Error(`Skeleton SQL changed: missing "${a.trim()}"`);
  // This union hangs in PGlite's GEOS on some inputs (e.g. Kathmandu, 100/task);
  // a 1e-9 degree grid size makes it robust.
  const sql = original.replace(
    SKELETON_ANCHORS.clip,
    SKELETON_ANCHORS.clip.replace(/\)$/, ", 1e-9)"),
  );
  const prefix = sql.slice(0, sql.indexOf(SKELETON_ANCHORS.cteEnd));
  return {
    input:
      prefix
        .replace("DROP TABLE IF EXISTS pg_temp.taskpolygons;", "")
        .replace(SKELETON_ANCHORS.create, "CREATE TEMP TABLE planner_skeleton_input AS (") +
      `\n  planner_end AS (SELECT 1)
      SELECT (ST_Dump(geom)).geom FROM aoi_minus_hulls);`,
    tasks: sql.replace(
      SKELETON_ANCHORS.call,
      "ST_Union((SELECT COALESCE(ST_Collect(geom), ST_SetSRID('GEOMETRYCOLLECTION EMPTY'::geometry, 4326)) FROM planner_skeleton_lines),",
    ),
  };
}

const skel = skeletonSql(skeleton);
export const SKELETON_INPUT = skel.input;
export const SKELETON_TASKS = skel.tasks;
export const SKELETON_PRE = [linearFeatures, groupBuildings, clusterBuildings];
export const SKELETON_POST = [alignment, extract];

// Mirrors area_splitter/db.py create_tables().
export const CREATE_TABLES = `
  CREATE TEMP TABLE project_aoi (id UUID DEFAULT gen_random_uuid() PRIMARY KEY, geom GEOMETRY(GEOMETRY, 4326));
  CREATE TEMP TABLE ways_poly (id SERIAL PRIMARY KEY, osm_id VARCHAR NULL, geom GEOMETRY(GEOMETRY, 4326) NOT NULL, tags JSONB NULL);
  CREATE TEMP TABLE ways_line (id SERIAL PRIMARY KEY, osm_id VARCHAR NULL, geom GEOMETRY(GEOMETRY, 4326) NOT NULL, tags JSONB NULL);
  CREATE INDEX idx_project_aoi_geom ON project_aoi USING GIST(geom);
  CREATE INDEX idx_ways_poly_geom ON ways_poly USING GIST(geom);
  CREATE INDEX idx_ways_line_geom ON ways_line USING GIST(geom);
`;

export const DROP_TABLES = [
  "lines_view",
  "buildings",
  "clusteredbuildings",
  "dumpedpoints",
  "lowfeaturecountpolygons",
  "voronois",
  "planner_skeleton_input",
  "planner_skeleton_lines",
  "my_taskpolygons",
  "taskpolygons",
  "unsimplifiedtaskpolygons",
  "splitpolygons",
  "polygonsnocount",
  "partition_tasks",
  "taskcounts",
  "splitline_union",
  "splitline_buffer",
  "project_aoi",
  "ways_poly",
  "ways_line",
  "grid_cells",
]
  .map((t) =>
    t === "lines_view" ? "DROP VIEW IF EXISTS lines_view;" : `DROP TABLE IF EXISTS ${t} CASCADE;`,
  )
  .join("\n");

export const LINES_VIEW = `
  CREATE TEMP VIEW lines_view AS
  SELECT w.tags, w.geom FROM ways_line w
  CROSS JOIN (SELECT geom FROM project_aoi LIMIT 1) p
  WHERE ST_Intersects(p.geom, w.geom);
`;

/** Substitute %(name)s placeholders, as splitter.py does. Values are validated by the caller. */
export function substitute(sql: string, params: Record<string, string | number>): string {
  return Object.entries(params).reduce((s, [k, v]) => s.replaceAll(`%(${k})s`, String(v)), sql);
}
