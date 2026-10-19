import type { Feature, FeatureCollection, LineString, Polygon } from "geojson";
import type { Area } from "../geo";
import type { Task } from "../taskPlan";
import { CREATE_TABLES, DROP_TABLES, LINES_VIEW, SQL_FILES, substitute } from "./sql";

/** The subset of PGlite used here, so tests can pass any instance. */
export interface Db {
  exec(sql: string): Promise<{ rows: Record<string, unknown>[] }[]>;
  query<T = Record<string, unknown>>(sql: string, params?: unknown[]): Promise<{ rows: T[] }>;
}

export type SplitAlgorithm = "DIVIDE_BY_SQUARE" | "SPLIT_BY_ROADS" | "AVG_BUILDING_VORONOI";

export interface SplitParams {
  cell_size?: number;
  num_buildings?: number;
  include_roads?: boolean;
  include_rivers?: boolean;
  include_railways?: boolean;
  include_aeroways?: boolean;
}

export interface SplitInput {
  aoi: Area;
  algorithm: SplitAlgorithm;
  params: SplitParams;
  features?: FeatureCollection | null;
  roads?: FeatureCollection | null;
}

type Progress = (msg: string) => void;
type Tags = Record<string, unknown>;

const LINEAR_KEYS = ["highway", "waterway", "railway", "aeroway"];
const BARRIERS: Record<string, string[]> = {
  barrier: ["fence", "wire_fence", "wall", "city_wall", "ditch"],
  natural: ["cliff"],
  man_made: ["embankment", "dyke", "dike"],
};

function tagsOf(props: unknown): Tags {
  let t = (props ?? {}) as Tags;
  if (typeof t.tags === "string") t = JSON.parse(t.tags);
  else if (t.tags && typeof t.tags === "object") t = t.tags as Tags;
  return t;
}

/** Port of splitter.py _is_linear_split_feature. */
export function isLinearSplitFeature(tags: Tags): boolean {
  if (LINEAR_KEYS.some((k) => k in tags)) return true;
  return Object.entries(BARRIERS).some(([k, vals]) =>
    vals.includes(
      String(tags[k] ?? "")
        .trim()
        .toLowerCase(),
    ),
  );
}

/** Bucket input features into building polygons and split lines (as _insert_split_sql_extract does). */
export function classify(features?: FeatureCollection | null, roads?: FeatureCollection | null) {
  const polys: { g: unknown; id: unknown; t: Tags }[] = [];
  const lines: { g: unknown; id: unknown; t: Tags }[] = [];
  const isLine = (f: Feature) =>
    f.geometry?.type === "LineString" || f.geometry?.type === "MultiLineString";
  for (const f of features?.features ?? []) {
    const t = tagsOf(f.properties);
    const id = f.properties?.osm_id ?? f.id ?? null;
    if (f.geometry?.type === "Polygon" || f.geometry?.type === "MultiPolygon") {
      // Any polygon the user provides is treated as a feature to map.
      polys.push({ g: f.geometry, id, t: { building: "yes", ...t } });
    } else if (isLine(f) && isLinearSplitFeature(t)) {
      lines.push({ g: f.geometry, id, t });
    }
  }
  for (const f of roads?.features ?? []) {
    if (!isLine(f)) continue;
    const t = tagsOf(f.properties);
    // Untagged lines in a roads file still count as split lines.
    lines.push({
      g: f.geometry,
      id: f.properties?.osm_id ?? null,
      t: isLinearSplitFeature(t) ? t : { ...t, highway: "road" },
    });
  }
  return { polys, lines };
}

const posNum = (v: unknown, name: string, max: number) => {
  const n = Number(v);
  if (!Number.isFinite(n) || n <= 0 || n > max)
    throw new Error(`${name} must be between 1 and ${max}`);
  return n;
};

/** WGS84 metres to degrees at a latitude (port of splitter.py meters_to_degrees). */
export function metresToDegrees(m: number, lat: number): [dLng: number, dLat: number] {
  const a = 6378137.0,
    f = 1 / 298.257223563,
    e2 = 2 * f - f * f;
  const s = Math.sin((lat * Math.PI) / 180);
  const n = a / Math.sqrt(1 - e2 * s * s);
  const mer = (a * (1 - e2)) / (1 - e2 * s * s) ** 1.5;
  const deg = 180 / Math.PI;
  return [(m / (n * Math.cos((lat * Math.PI) / 180))) * deg, (m / mer) * deg];
}

async function loadInputs(db: Db, input: SplitInput) {
  await db.exec(DROP_TABLES);
  await db.exec(CREATE_TABLES);
  await db.query(
    `INSERT INTO project_aoi (geom) VALUES (ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON($1), 4326)))`,
    [JSON.stringify(input.aoi)],
  );
  const { polys, lines } = classify(input.features, input.roads);
  for (const [table, rows] of [
    ["ways_poly", polys],
    ["ways_line", lines],
  ] as const) {
    if (!rows.length) continue;
    await db.query(
      `INSERT INTO ${table} (geom, osm_id, tags)
       SELECT ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(e->>'g'), 4326)), e->>'id', e->'t'
       FROM jsonb_array_elements($1::jsonb) e`,
      [JSON.stringify(rows.map((r) => ({ ...r, g: JSON.stringify(r.g) })))],
    );
  }
  await db.exec(LINES_VIEW);
  return { buildings: polys.length, lines: lines.length };
}

async function gridSplit(db: Db, cellSize: number) {
  const { rows } = await db.query<{ lat: number }>(
    `SELECT ST_Y(ST_Centroid(geom)) AS lat FROM project_aoi`,
  );
  const [dx, dy] = metresToDegrees(cellSize, rows[0].lat);
  await db.query(
    `CREATE TEMP TABLE grid_cells AS
     WITH a AS (SELECT geom FROM project_aoi LIMIT 1),
     b AS (SELECT ST_XMin(geom) x0, ST_YMin(geom) y0, ST_XMax(geom) x1, ST_YMax(geom) y1 FROM a),
     cells AS (
       SELECT ST_MakeEnvelope(x0 + i * $1, y0 + j * $2, x0 + (i + 1) * $1, y0 + (j + 1) * $2, 4326) AS cell
       FROM b, generate_series(0, floor((x1 - x0) / $1)::int) i, generate_series(0, floor((y1 - y0) / $2)::int) j
     ),
     clipped AS (
       SELECT ST_CollectionExtract(ST_Intersection(c.cell, a.geom), 3) AS geom
       FROM cells c, a WHERE ST_Intersects(c.cell, a.geom)
     )
     SELECT row_number() OVER () AS id, geom, ST_Area(geom::geography) AS area
     FROM clipped WHERE NOT ST_IsEmpty(geom)`,
    [dx, dy],
  );
  // Merge slivers into the neighbour with the longest shared edge, as splitter.py does.
  await db.exec(`
    DO $$
    DECLARE small RECORD; nb RECORD;
    BEGIN
      FOR small IN SELECT * FROM grid_cells WHERE area < ${0.35 * cellSize ** 2} ORDER BY area LOOP
        FOR nb IN
          SELECT id, ST_Length(ST_Intersection(small.geom, g.geom)) AS shared FROM grid_cells g
          WHERE g.id <> small.id AND g.area >= ${0.35 * cellSize ** 2} AND ST_Touches(small.geom, g.geom)
            AND ST_GeometryType(ST_Intersection(small.geom, g.geom)) <> 'ST_Point'
          ORDER BY shared DESC LIMIT 1
        LOOP
          UPDATE grid_cells SET geom = ST_Union(geom, small.geom) WHERE id = nb.id;
          DELETE FROM grid_cells WHERE id = small.id;
        END LOOP;
      END LOOP;
    END $$;`);
  const { rows: out } = await db.query<{ fc: FeatureCollection }>(
    `SELECT jsonb_build_object('type', 'FeatureCollection', 'features',
       COALESCE(jsonb_agg(jsonb_build_object('type', 'Feature', 'geometry', ST_AsGeoJSON(geom)::jsonb, 'properties', '{}'::jsonb) ORDER BY id), '[]'::jsonb)) AS fc
     FROM grid_cells`,
  );
  return out[0].fc;
}

async function sqlSplit(
  db: Db,
  algorithm: "SPLIT_BY_ROADS" | "AVG_BUILDING_VORONOI",
  p: SplitParams,
  progress: Progress,
) {
  const bool = (v: boolean | undefined) => (v === false ? "FALSE" : "TRUE");
  const params = {
    include_roads: bool(p.include_roads),
    include_rivers: bool(p.include_rivers),
    include_railways: bool(p.include_railways),
    include_aeroways: bool(p.include_aeroways),
  };
  const numBuildings =
    algorithm === "AVG_BUILDING_VORONOI"
      ? Math.round(posNum(p.num_buildings, "Buildings per task", 10000))
      : 0;
  await db.exec(
    `SET area_splitter.num_buildings = ${numBuildings}; SET area_splitter.num_enumerators = 0;`,
  );
  let last: { rows: Record<string, unknown>[] }[] = [];
  const files = SQL_FILES[algorithm];
  for (const [i, sql] of files.entries()) {
    progress(`Running step ${i + 1} of ${files.length}`);
    last = await db.exec(substitute(sql, params));
  }
  const row = last.at(-1)?.rows[0];
  const fc = (row ? Object.values(row)[0] : null) as FeatureCollection | null;
  return { type: "FeatureCollection", features: fc?.features ?? [] } as FeatureCollection;
}

/** Split polygons into single Polygons, drop slivers, and count buildings by centroid. */
async function normalise(db: Db, fc: FeatureCollection, countBuildings: boolean): Promise<Task[]> {
  const { rows } = await db.query<{ g: Polygon; n: number }>(
    `SELECT ST_AsGeoJSON(d.geom, 7)::jsonb AS g,
       (SELECT count(*) FROM ways_poly b WHERE b.geom && d.geom AND ST_Contains(d.geom, ST_PointOnSurface(b.geom)))::int AS n
     FROM jsonb_array_elements($1::jsonb) e,
       LATERAL ST_Dump(ST_CollectionExtract(ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(e->>'geometry'), 4326)), 3)) d
     WHERE ST_Area(d.geom::geography) > 1`,
    [
      JSON.stringify(
        fc.features
          .filter((f) => f.geometry)
          .map((f) => ({ geometry: JSON.stringify(f.geometry) })),
      ),
    ],
  );
  return rows.map((r, i) => ({
    type: "Feature",
    geometry: r.g,
    properties: countBuildings ? { task_id: i + 1, building_count: r.n } : { task_id: i + 1 },
  }));
}

export async function split(
  db: Db,
  input: SplitInput,
  progress: Progress = () => {},
): Promise<Task[]> {
  progress("Loading data");
  const counts = await loadInputs(db, input);
  let fc: FeatureCollection;
  if (input.algorithm === "DIVIDE_BY_SQUARE") {
    progress("Building grid");
    fc = await gridSplit(db, posNum(input.params.cell_size, "Cell size (m)", 100_000));
  } else if (input.algorithm === "SPLIT_BY_ROADS") {
    if (!counts.lines) throw new Error("No roads or other split lines found in the area");
    fc = await sqlSplit(db, "SPLIT_BY_ROADS", input.params, progress);
  } else if (input.algorithm === "AVG_BUILDING_VORONOI") {
    if (!counts.buildings) throw new Error("Upload buildings (or other polygon features) first");
    fc = await sqlSplit(db, "AVG_BUILDING_VORONOI", input.params, progress);
  } else {
    throw new Error(`Unknown algorithm ${input.algorithm}`);
  }
  progress("Tidying tasks");
  const tasks = await normalise(db, fc, counts.buildings > 0);
  await db.exec(DROP_TABLES);
  if (!tasks.length) throw new Error("Splitting produced no tasks");
  return tasks;
}

/** Union polygons; fails unless the result is one Polygon. */
export async function merge(db: Db, polygons: Polygon[]): Promise<Polygon> {
  const { rows } = await db.query<{ g: Polygon }>(
    `SELECT ST_AsGeoJSON(ST_UnaryUnion(ST_Collect(ST_SnapToGrid(ST_MakeValid(ST_GeomFromGeoJSON(e #>> '{}')), 1e-7))), 7)::jsonb AS g
     FROM jsonb_array_elements($1::jsonb) e`,
    [JSON.stringify(polygons.map((p) => JSON.stringify(p)))],
  );
  const g = rows[0]?.g;
  if (g?.type !== "Polygon") throw new Error("Only touching tasks can be merged");
  return g;
}

/** Cut a polygon with a line; fails unless the line crosses it. */
export async function splitByLine(db: Db, polygon: Polygon, line: LineString): Promise<Polygon[]> {
  const { rows } = await db.query<{ g: Polygon }>(
    `SELECT ST_AsGeoJSON(d.geom, 7)::jsonb AS g
     FROM ST_Dump(ST_Split(ST_MakeValid(ST_GeomFromGeoJSON($1)), ST_GeomFromGeoJSON($2))) d
     WHERE ST_GeometryType(d.geom) = 'ST_Polygon'`,
    [JSON.stringify(polygon), JSON.stringify(line)],
  );
  if (rows.length < 2) throw new Error("Draw a line that crosses the task from edge to edge");
  return rows.map((r) => r.g);
}
