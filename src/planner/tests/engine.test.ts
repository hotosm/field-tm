import { readFileSync } from "node:fs";
import { beforeAll, describe, expect, it } from "vitest";
import type { FeatureCollection } from "geojson";
import { createDb } from "../src/lib/engine/db";
import { classify, merge, split, splitByLine, type Db } from "../src/lib/engine/splitter";
import { toArea } from "../src/lib/geo";
import { validate, makePlan } from "../src/lib/taskPlan";

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
    const total = tasks.reduce((s, t) => s + (t.properties.building_count ?? 0), 0);
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
    ).rejects.toThrow(/buildings/);
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
