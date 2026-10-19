// Timing spike: SPIKE=1 pnpm vitest run tests/spike.test.ts
import { readFileSync } from "node:fs";
import { describe, it } from "vitest";
import type { Feature, FeatureCollection } from "geojson";
import { createDb } from "../src/lib/engine/db";
import { split, type SplitInput } from "../src/lib/engine/splitter";
import { squareAround, toArea } from "../src/lib/geo";

function synthetic(
  n: number,
  centre: [number, number],
): { aoi: SplitInput["aoi"]; features: FeatureCollection } {
  const side = Math.ceil(Math.sqrt(n));
  const step = 20 / 111_320;
  const s = 8 / 111_320;
  const [x0, y0] = [centre[0] - (side * step) / 2, centre[1] - (side * step) / 2];
  const features: Feature[] = [];
  for (let i = 0; i < n; i++) {
    const x = x0 + (i % side) * step + Math.random() * s;
    const y = y0 + Math.floor(i / side) * step + Math.random() * s;
    features.push({
      type: "Feature",
      properties: { building: "yes" },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [x, y],
            [x + s, y],
            [x + s, y + s],
            [x, y + s],
            [x, y],
          ],
        ],
      },
    });
  }
  for (let k = 1; k < 4; k++) {
    const x = x0 + (k * side * step) / 4 + step / 2;
    const y = y0 + (k * side * step) / 4 + step / 2;
    features.push({
      type: "Feature",
      properties: { highway: "primary" },
      geometry: {
        type: "LineString",
        coordinates: [
          [x, y0 - 10 * step],
          [x, y0 + side * step + 10 * step],
        ],
      },
    });
    features.push({
      type: "Feature",
      properties: { highway: "secondary" },
      geometry: {
        type: "LineString",
        coordinates: [
          [x0 - 10 * step, y],
          [x0 + side * step + 10 * step, y],
        ],
      },
    });
  }
  return {
    aoi: squareAround(centre, side * 20 + 40),
    features: { type: "FeatureCollection", features },
  };
}

describe.skipIf(!process.env.SPIKE)("spike timings", () => {
  it("runs", async () => {
    let t = performance.now();
    const db = await createDb();
    const lap = (label: string, extra = "") => {
      console.log(`${label}: ${Math.round(performance.now() - t)} ms ${extra}`);
      t = performance.now();
    };
    lap("PGlite + PostGIS init");
    const td = (f: string) =>
      JSON.parse(
        readFileSync(
          new URL(`../../backend/packages/area-splitter/tests/testdata/${f}`, import.meta.url),
          "utf8",
        ),
      );
    const k = { aoi: toArea(td("kathmandu.geojson")), features: td("kathmandu_extract.geojson") };
    for (const [name, input] of [
      ["kathmandu (667 buildings)", k],
      ["synthetic 10k", synthetic(10_000, [36.8, -1.28])],
    ] as const) {
      let r = await split(db, {
        ...input,
        algorithm: "DIVIDE_BY_SQUARE",
        params: { cell_size: 50 },
      });
      lap(
        `${name} grid 50m`,
        `${r.length} tasks, ${r.filter((x) => x.properties.building_count).length} non-empty`,
      );
      r = await split(db, { ...input, algorithm: "SPLIT_BY_ROADS", params: {} });
      lap(`${name} roads`, `${r.length} tasks`);
      for (const nb of [5, 100]) {
        r = await split(db, {
          ...input,
          algorithm: "AVG_BUILDING_VORONOI",
          params: { num_buildings: nb },
        });
        const counts = r.map((x) => x.properties.building_count ?? 0);
        lap(
          `${name} voronoi ${nb}/task`,
          `${r.length} tasks, buildings/task min ${Math.min(...counts)} max ${Math.max(...counts)}`,
        );
      }
    }
  }, 900_000);
});
