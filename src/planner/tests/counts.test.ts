import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import type { FeatureCollection, Polygon } from "geojson";
import { featurePoints, featuresInside, withFeatureCounts } from "../src/lib/counts";
import { replaceTasks } from "../src/lib/planEdit";
import type { Task } from "../src/lib/taskPlan";

const square = (x0: number, y0: number, x1: number, y1: number): Polygon => ({
  type: "Polygon",
  coordinates: [
    [
      [x0, y0],
      [x1, y0],
      [x1, y1],
      [x0, y1],
      [x0, y0],
    ],
  ],
});
const building = (x: number, y: number) => ({
  type: "Feature" as const,
  properties: {},
  geometry: square(x - 0.1, y - 0.1, x + 0.1, y + 0.1),
});

describe("building counts", () => {
  const fc: FeatureCollection = {
    type: "FeatureCollection",
    features: [building(1, 1), building(3, 1), building(3, 3)],
  };
  const points = featurePoints(fc);

  it("uses one point per building", () => {
    expect(points).toEqual([
      [1, 1],
      [3, 1],
      [3, 3],
    ]);
  });

  it("counts points inside a polygon, excluding holes", () => {
    const withHole: Polygon = {
      type: "Polygon",
      coordinates: [square(0, 0, 4, 4).coordinates[0], square(2.5, 2.5, 3.5, 3.5).coordinates[0]],
    };
    expect(featuresInside(points, square(0, 0, 4, 4))).toBe(3);
    expect(featuresInside(points, withHole)).toBe(2);
  });

  it("recounts after splitting a task in two", () => {
    const tasks: Task[] = [
      {
        type: "Feature",
        geometry: square(0, 0, 4, 4),
        properties: { task_id: 1, feature_count: 3 },
      },
    ];
    const split = replaceTasks(tasks, [1], [square(0, 0, 2, 4), square(2, 0, 4, 4)]);
    expect(withFeatureCounts(split, points).map((t) => t.properties.feature_count)).toEqual([1, 2]);
  });

  it("matches the engine's counts for the Kathmandu fixture", () => {
    const extract = JSON.parse(
      readFileSync(
        new URL(
          "../../backend/packages/area-splitter/tests/testdata/kathmandu_extract.geojson",
          import.meta.url,
        ),
        "utf8",
      ),
    );
    const aoi = JSON.parse(
      readFileSync(
        new URL(
          "../../backend/packages/area-splitter/tests/testdata/kathmandu.geojson",
          import.meta.url,
        ),
        "utf8",
      ),
    );
    const area: Polygon = aoi.features?.[0]?.geometry ?? aoi.geometry ?? aoi;
    expect(featuresInside(featurePoints(extract), area)).toBe(667);
  });
});
