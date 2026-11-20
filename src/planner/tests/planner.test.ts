import { beforeEach, describe, expect, it, vi } from "vitest";
import type { FeatureCollection } from "geojson";
import { Planner } from "../src/lib/planner.svelte";
import { engine } from "../src/lib/engine/client";
import { fetchRoads } from "../src/lib/io/postpass";
import type { Task } from "../src/lib/taskPlan";

vi.mock("../src/lib/engine/client", () => ({ engine: { split: vi.fn(async () => []) } }));
vi.mock("../src/lib/io/postpass", async (actual) => ({
  ...(await actual<typeof import("../src/lib/io/postpass")>()),
  fetchRoads: vi.fn(async () => roads),
}));

const roads: FeatureCollection = { type: "FeatureCollection", features: [] };

const sq = (x: number): Task["geometry"] => ({
  type: "Polygon",
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

describe("Planner", () => {
  it("clears the selection after assigning, so the next task can be picked", () => {
    const planner = new Planner("test");
    planner.load({
      plan: {
        type: "FeatureCollection",
        task_plan_version: 1,
        algorithm: "MANUAL",
        params: {},
        features: [1, 2].map((id) => ({
          type: "Feature",
          geometry: sq(id),
          properties: { task_id: id },
        })),
      },
    });
    planner.selected = [1, 2];
    planner.assignSelected({ assigned_group: "north" });
    expect(planner.selected).toEqual([]);
    expect(planner.tasks.map((t) => t.properties.assigned_group)).toEqual(["north", "north"]);
  });
});

describe("Planner.split", () => {
  // About 1 km across, small enough to fetch roads for.
  const small = sq(0);
  small.coordinates[0] = small.coordinates[0].map(([x, y]) => [x / 100, y / 100]);

  beforeEach(() => vi.clearAllMocks());

  it("fetches roads before a road-based split", async () => {
    const planner = new Planner("test");
    planner.load({ aoi: small });
    await planner.split("SPLIT_BY_ROADS", {});
    expect(fetchRoads).toHaveBeenCalledOnce();
    expect(vi.mocked(engine.split).mock.calls[0][0].roads).toBe(roads);
  });

  it("reuses fetched roads until the area changes", async () => {
    const planner = new Planner("test");
    planner.load({ aoi: small });
    await planner.split("AVG_BUILDING_VORONOI", { num_buildings: 10 });
    await planner.split("SPLIT_BY_ROADS", {});
    expect(fetchRoads).toHaveBeenCalledOnce();
    planner.commit({ aoi: { ...small }, tasks: [] });
    await planner.split("SPLIT_BY_ROADS", {});
    expect(fetchRoads).toHaveBeenCalledTimes(2);
  });

  it("drops OSM roads for an old area when splitting a new, larger one", async () => {
    const planner = new Planner("test");
    planner.load({ aoi: small });
    await planner.split("SPLIT_BY_ROADS", {});
    planner.commit({ aoi: sq(0), tasks: [] });
    expect(planner.currentRoads).toBeNull();
    await planner.split("AVG_BUILDING_VORONOI", { num_buildings: 10 });
    expect(fetchRoads).toHaveBeenCalledOnce();
    expect(vi.mocked(engine.split).mock.calls[1][0].roads).toBeNull();
  });

  it("still treats OSM roads as stale after importing a plan for another area", async () => {
    const planner = new Planner("test");
    planner.load({ aoi: small });
    await planner.split("SPLIT_BY_ROADS", {});
    planner.load({ aoi: sq(0), features: planner.features, roads: planner.roads });
    expect(planner.currentRoads).toBeNull();
  });

  it("keeps the current tasks when the road download fails", async () => {
    const planner = new Planner("test");
    planner.load({ aoi: small });
    await planner.split("DIVIDE_BY_SQUARE", { cell_size: 100 });
    const before = planner.tasks;
    vi.mocked(fetchRoads).mockRejectedValueOnce(new Error("OSM roads could not be downloaded"));
    await planner.split("SPLIT_BY_ROADS", {});
    expect(planner.error).toMatch(/could not be downloaded/);
    expect(planner.tasks).toBe(before);
  });

  it("uses uploaded roads instead of fetching, even for large areas", async () => {
    const planner = new Planner("test");
    planner.load({ aoi: sq(0) });
    planner.setData("roads", roads);
    await planner.split("SPLIT_BY_ROADS", {});
    expect(fetchRoads).not.toHaveBeenCalled();
    expect(planner.error).toBeNull();
    expect(vi.mocked(engine.split).mock.calls[0][0].roads).toBe(roads);
  });

  it("does not fetch roads for a square grid", async () => {
    const planner = new Planner("test");
    planner.load({ aoi: small });
    await planner.split("DIVIDE_BY_SQUARE", { cell_size: 100 });
    expect(fetchRoads).not.toHaveBeenCalled();
  });

  it("splits large areas by features without roads, but not by roads", async () => {
    const planner = new Planner("test");
    planner.load({ aoi: sq(0) });
    await planner.split("AVG_BUILDING_VORONOI", { num_buildings: 10 });
    expect(engine.split).toHaveBeenCalledOnce();
    await planner.split("SPLIT_BY_ROADS", {});
    expect(planner.error).toMatch(/too large/);
    expect(fetchRoads).not.toHaveBeenCalled();
  });
});
