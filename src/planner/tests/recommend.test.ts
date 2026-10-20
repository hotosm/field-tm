import { describe, expect, it } from "vitest";
import type { Polygon } from "geojson";
import { estimateTasks, recommend } from "../src/lib/recommend";

// ~1 km square near the equator.
const aoi: Polygon = {
  type: "Polygon",
  coordinates: [
    [
      [0, 0],
      [0.009, 0],
      [0.009, 0.009],
      [0, 0.009],
      [0, 0],
    ],
  ],
};

describe("estimateTasks", () => {
  it("uses the number of tasks when given", () => {
    expect(estimateTasks(aoi, "AVG_BUILDING_SKELETON", { num_enumerators: 7 }, 500)).toBe(7);
  });

  it("divides features by features per task", () => {
    expect(estimateTasks(aoi, "AVG_BUILDING_VORONOI", { num_buildings: 50 }, 501)).toBe(11);
  });

  it("has no estimate for roads", () => {
    expect(estimateTasks(aoi, "SPLIT_BY_ROADS", {}, 500)).toBeNull();
  });
});

describe("recommend", () => {
  it("splits by roads when there are only roads", () => {
    expect(recommend(aoi, 0, 10).algorithm).toBe("SPLIT_BY_ROADS");
  });
});
