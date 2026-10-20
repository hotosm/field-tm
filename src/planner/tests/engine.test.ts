import { readFileSync } from "node:fs";
import { beforeAll, describe, expect, it } from "vitest";
import type { FeatureCollection } from "geojson";
import { createDb } from "../src/lib/engine/db";
import { classify, merge, split, splitByLine, type Db } from "../src/lib/engine/splitter";
import { areaM2, featurePoint, toArea } from "../src/lib/geo";
import { validate, makePlan, type Task } from "../src/lib/taskPlan";
import { SKELETON_ANCHORS, VORONOI_UNION_ANCHOR } from "../src/lib/engine/sql";

const testdata = (f: string) =>
  JSON.parse(
    readFileSync(
      new URL(`../../backend/packages/area-splitter/tests/testdata/${f}`, import.meta.url),
      "utf8",
    ),
  );

const aoi = toArea(testdata("kathmandu.geojson"));
const extract: FeatureCollection = testdata("kathmandu_extract.geojson");

let db: Db;
beforeAll(async () => {
  db = await createDb();
});

describe("classify", () => {
  it("buckets buildings and linear features", () => {
    const { polys, lines } = classify(extract);
    expect(polys).toHaveLength(667);
    expect(lines).toHaveLength(22);
  });
});

describe("split", () => {
  it("grid covers the AOI and produces a valid plan", async () => {
    const tasks = await split(db, {
      aoi,
      algorithm: "DIVIDE_BY_SQUARE",
      params: { cell_size: 50 },
    });
    expect(tasks.length).toBeGreaterThan(60);
    expect(validate(makePlan(tasks, "DIVIDE_BY_SQUARE"))).toEqual([]);
  });

  it("grid counts buildings", async () => {
    const tasks = await split(db, {
      aoi,
      algorithm: "DIVIDE_BY_SQUARE",
      params: { cell_size: 200 },
      features: extract,
    });
    const total = tasks.reduce((s, t) => s + (t.properties.feature_count ?? 0), 0);
    expect(total).toBe(667);
  });

  it("splits by roads with the shared SQL", async () => {
    const tasks = await split(db, {
      aoi,
      algorithm: "SPLIT_BY_ROADS",
      params: {},
      features: extract,
    });
    expect(tasks.length).toBeGreaterThanOrEqual(1);
    expect(tasks.every((t) => t.geometry.type === "Polygon")).toBe(true);
  });

  it("splits by average buildings (Voronoi) with the shared SQL", async () => {
    const tasks = await split(db, {
      aoi,
      algorithm: "AVG_BUILDING_VORONOI",
      params: { num_buildings: 5 },
      features: extract,
    });
    expect(tasks.length).toBeGreaterThanOrEqual(60);
    expect(validate(makePlan(tasks, "AVG_BUILDING_VORONOI"))).toEqual([]);
  });

  it("rejects Voronoi without buildings", async () => {
    await expect(
      split(db, { aoi, algorithm: "AVG_BUILDING_VORONOI", params: { num_buildings: 5 } }),
    ).rejects.toThrow(/features/);
  });
});

describe("points and lines as features", () => {
  // Building centroids stand in for point data such as water points or shops.
  const points: FeatureCollection = {
    type: "FeatureCollection",
    features: extract.features
      .filter((f) => f.geometry.type === "Polygon")
      .map((f) => ({
        type: "Feature",
        properties: {},
        geometry: { type: "Point", coordinates: featurePoint(f.geometry)! },
      })),
  };

  it("treats points as features and a lines-only file as features", () => {
    expect(classify(points).polys).toHaveLength(667);
    const lines = {
      ...extract,
      features: extract.features.filter((f) => f.geometry.type === "LineString"),
    };
    expect(classify(lines).polys).toHaveLength(lines.features.length);
    expect(classify(lines).lines).toHaveLength(0);
    // Mixed with buildings, the same lines are split lines.
    expect(classify(extract).lines).toHaveLength(22);
  });

  for (const algorithm of ["AVG_BUILDING_VORONOI", "AVG_BUILDING_SKELETON"] as const) {
    it(`splits points with ${algorithm} and counts every point`, async () => {
      const fresh = await createDb();
      const tasks = await split(fresh, {
        aoi,
        algorithm,
        params: { num_buildings: 50 },
        features: points,
      });
      expect(tasks.length).toBeGreaterThan(5);
      expect(tasks.reduce((s, t) => s + (t.properties.feature_count ?? 0), 0)).toBe(667);
      expect(validate(makePlan(tasks, algorithm))).toEqual([]);
    }, 300_000);
  }

  it("drops tasks with nothing to map when asked", async () => {
    const fresh = await createDb();
    const params = { cell_size: 100 };
    const sparse = { ...points, features: points.features.slice(0, 20) };
    const all = await split(fresh, {
      aoi,
      algorithm: "DIVIDE_BY_SQUARE",
      params,
      features: sparse,
    });
    const kept = await split(fresh, {
      aoi,
      algorithm: "DIVIDE_BY_SQUARE",
      params: { ...params, drop_empty: true },
      features: sparse,
    });
    expect(all.some((t) => t.properties.feature_count === 0)).toBe(true);
    expect(kept.every((t) => (t.properties.feature_count ?? 0) > 0)).toBe(true);
    expect(kept.map((t) => t.properties.task_id)).toEqual(kept.map((_, i) => i + 1));
  }, 120_000);
});

describe("voronoi with OSM roads", () => {
  // Buildings plus Overpass roads used to break PGlite's GEOS in the task
  // boundary union, giving "no tasks" and then ERRORDATA_STACK_SIZE errors.
  const roads: FeatureCollection = JSON.parse(
    readFileSync(new URL("./fixtures/kathmandu_roads.geojson", import.meta.url), "utf8"),
  );
  const buildings: FeatureCollection = {
    ...extract,
    features: extract.features.filter((f) => f.geometry.type !== "LineString"),
  };

  it("finds its replacement anchor in the backend SQL", () => {
    const sql = readFileSync(
      new URL(
        "../../backend/packages/area-splitter/area_splitter/algorithms/avg_building_voronoi.sql",
        import.meta.url,
      ),
      "utf8",
    );
    expect(sql).toContain(VORONOI_UNION_ANCHOR);
  });

  it("splits buildings with roads, and the engine still works afterwards", async () => {
    const fresh = await createDb();
    const tasks = await split(fresh, {
      aoi,
      algorithm: "AVG_BUILDING_VORONOI",
      params: { num_buildings: 10 },
      features: buildings,
      roads,
    });
    expect(tasks.length).toBeGreaterThan(30);
    expect(validate(makePlan(tasks, "AVG_BUILDING_VORONOI"))).toEqual([]);
    const again = await split(fresh, {
      aoi,
      algorithm: "DIVIDE_BY_SQUARE",
      params: { cell_size: 200 },
    });
    expect(again.length).toBeGreaterThan(0);
  }, 120_000);

  it("splits by every road, merging slivers", async () => {
    const fresh = await createDb();
    const main = await split(fresh, {
      aoi,
      algorithm: "SPLIT_BY_ROADS",
      params: { include_minor_roads: false },
      roads,
    });
    const all = await split(fresh, { aoi, algorithm: "SPLIT_BY_ROADS", params: {}, roads });
    expect(all.length).toBeGreaterThan(main.length);
    expect(all.every((t) => areaM2(t.geometry) >= 1000)).toBe(true);
    expect(validate(makePlan(all, "SPLIT_BY_ROADS"))).toEqual([]);
  }, 120_000);

  it("makes exactly the requested number of tasks", async () => {
    const fresh = await createDb();
    for (const [algorithm, n] of [
      ["AVG_BUILDING_VORONOI", 3],
      ["AVG_BUILDING_VORONOI", 12],
      // Fewer tasks than road-bounded blocks, so merges must cross roads.
      ["AVG_BUILDING_SKELETON", 2],
    ] as const) {
      const tasks = await split(fresh, {
        aoi,
        algorithm,
        params: { num_enumerators: n, drop_empty: true },
        features: buildings,
        roads,
      });
      expect(tasks).toHaveLength(n);
    }
  }, 300_000);

  it("refuses more tasks than features", async () => {
    await expect(
      split(db, {
        aoi,
        algorithm: "AVG_BUILDING_VORONOI",
        params: { num_enumerators: 10_000 },
        features: buildings,
      }),
    ).rejects.toThrow(/at most the number of features/);
  });
});

describe("straight skeleton", () => {
  it("finds its replacement anchors in the backend SQL", () => {
    const sql = readFileSync(
      new URL(
        "../../backend/packages/area-splitter/area_splitter/algorithms/avg_building_straight_skeleton.sql",
        import.meta.url,
      ),
      "utf8",
    );
    for (const a of Object.values(SKELETON_ANCHORS)) expect(sql).toContain(a);
  });

  /** Union area, summed area and area outside the AOI, in m². */
  async function areas(tasks: Task[]) {
    const { rows } = await db.query<{ u: number; s: number; out: number; valid: boolean }>(
      `WITH t AS (SELECT ST_SetSRID(ST_GeomFromGeoJSON(e #>> '{}'), 4326) g FROM jsonb_array_elements($1::jsonb) e),
         a AS (SELECT ST_SetSRID(ST_GeomFromGeoJSON($2), 4326) g)
       SELECT ST_Area(ST_Union(t.g)::geography) u, sum(ST_Area(t.g::geography)) s,
         ST_Area(ST_Difference(ST_Union(t.g), (SELECT g FROM a))::geography) out, bool_and(ST_IsValid(t.g)) valid
       FROM t`,
      [JSON.stringify(tasks.map((t) => JSON.stringify(t.geometry))), JSON.stringify(aoi)],
    );
    return rows[0];
  }

  it("splits Kathmandu like the backend", async () => {
    const tasks = await split(db, {
      aoi,
      algorithm: "AVG_BUILDING_SKELETON",
      params: { num_buildings: 5 },
      features: extract,
    });
    // As test_split_by_sql_ftm_with_extract (skeleton is the backend default).
    expect(tasks.length).toBeGreaterThanOrEqual(60);
    expect(validate(makePlan(tasks, "AVG_BUILDING_SKELETON"))).toEqual([]);
    const total = tasks.reduce((s, t) => s + (t.properties.feature_count ?? 0), 0);
    expect(total).toBe(667);
    const r = await areas(tasks);
    expect(r.valid).toBe(true);
    expect(Math.abs(r.s - r.u) / r.u).toBeLessThan(0.02);
    expect(r.out).toBeLessThan(r.u * 0.02);
  });

  it("does not hang on large clusters (GEOS union workaround)", async () => {
    const tasks = await split(db, {
      aoi,
      algorithm: "AVG_BUILDING_SKELETON",
      params: { num_buildings: 100 },
      features: extract,
    });
    expect(tasks.length).toBeGreaterThanOrEqual(4);
  });

  it("refuses inputs that would be too slow", async () => {
    const b = extract.features.find((f) => f.geometry.type === "Polygon")!;
    const many: FeatureCollection = {
      type: "FeatureCollection",
      features: Array.from({ length: 5001 }, () => b),
    };
    await expect(
      split(db, {
        aoi,
        algorithm: "AVG_BUILDING_SKELETON",
        params: { num_buildings: 10 },
        features: many,
      }),
    ).rejects.toThrow(/limited to 5000/);
    await expect(
      split(db, {
        aoi,
        algorithm: "AVG_BUILDING_SKELETON",
        params: { num_buildings: 2 },
        features: extract,
      }),
    ).rejects.toThrow(/limited to about 250 tasks/);
  });
});

describe("edit operations", () => {
  const sq = (x: number) => ({
    type: "Polygon" as const,
    coordinates: [
      [
        [x, 0],
        [x + 1, 0],
        [x + 1, 1],
        [x, 1],
        [x, 0],
      ],
    ],
  });

  it("merges touching polygons", async () => {
    const g = await merge(db, [sq(0), sq(1)]);
    expect(g.type).toBe("Polygon");
  });

  it("refuses to merge disjoint polygons", async () => {
    await expect(merge(db, [sq(0), sq(5)])).rejects.toThrow(/touching/);
  });

  it("splits a polygon with a crossing line", async () => {
    const parts = await splitByLine(db, sq(0), {
      type: "LineString",
      coordinates: [
        [0.5, -1],
        [0.5, 2],
      ],
    });
    expect(parts).toHaveLength(2);
    await expect(
      splitByLine(db, sq(0), {
        type: "LineString",
        coordinates: [
          [5, 5],
          [6, 6],
        ],
      }),
    ).rejects.toThrow();
  });
});
