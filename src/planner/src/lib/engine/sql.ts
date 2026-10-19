// Splitting SQL shared with the backend area-splitter package (not copied).
import linearFeatures from "@algorithms/common/1-linear-features.sql?raw";
import groupBuildings from "@algorithms/common/2-group-buildings.sql?raw";
import clusterBuildings from "@algorithms/common/3-cluster-buildings.sql?raw";
import alignment from "@algorithms/common/5-alignment.sql?raw";
import extract from "@algorithms/common/6-extract.sql?raw";
import voronoi from "@algorithms/avg_building_voronoi.sql?raw";
import splitByRoads from "@algorithms/split_by_roads.sql?raw";

export const SQL_FILES = {
  SPLIT_BY_ROADS: [linearFeatures, splitByRoads],
  AVG_BUILDING_VORONOI: [
    linearFeatures,
    groupBuildings,
    clusterBuildings,
    voronoi,
    alignment,
    extract,
  ],
} as const;

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
  "taskpolygons",
  "unsimplifiedtaskpolygons",
  "splitpolygons",
  "polygonsnocount",
  "partition_tasks",
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
