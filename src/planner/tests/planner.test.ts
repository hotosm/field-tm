import { describe, expect, it } from "vitest";
import { Planner } from "../src/lib/planner.svelte";
import type { Task } from "../src/lib/taskPlan";

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
