import { describe, expect, it } from "vitest";
import { assign, removeTasks, replaceTasks } from "../src/lib/planEdit";
import { recommend, gridSize } from "../src/lib/recommend";
import { squareAround } from "../src/lib/geo";
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
const tasks: Task[] = [1, 2, 3, 4].map((id) => ({
  type: "Feature",
  geometry: sq(id),
  properties: { task_id: id, assigned_group: `g${id}`, building_count: id },
}));

describe("plan edits", () => {
  it("replaces tasks in place, keeps the first assignment and renumbers", () => {
    const out = replaceTasks(tasks, [2, 3], [sq(9)], [5]);
    expect(out.map((t) => t.properties)).toEqual([
      { task_id: 1, assigned_group: "g1", building_count: 1 },
      { task_id: 2, assigned_group: "g2", building_count: 5 },
      { task_id: 3, assigned_group: "g4", building_count: 4 },
    ]);
  });

  it("splits one task into several", () => {
    const out = replaceTasks(tasks, [1], [sq(7), sq(8)]);
    expect(out.map((t) => [t.properties.task_id, t.properties.assigned_group])).toEqual([
      [1, "g1"],
      [2, "g1"],
      [3, "g2"],
      [4, "g3"],
      [5, "g4"],
    ]);
  });

  it("removes and renumbers", () => {
    expect(
      removeTasks(tasks, [1, 3]).map((t) => [t.properties.task_id, t.properties.assigned_group]),
    ).toEqual([
      [1, "g2"],
      [2, "g4"],
    ]);
  });

  it("assigns, leaves undefined fields and clears empty ones", () => {
    const out = assign(tasks, [1, 2], {
      assigned_to: "Ana",
      assigned_group: "",
      comment: undefined,
    });
    expect(out[0].properties).toEqual({ task_id: 1, assigned_to: "Ana", building_count: 1 });
    expect(out[2]).toBe(tasks[2]);
  });
});

describe("recommend", () => {
  it("suggests a grid of about 100 cells without data", () => {
    const aoi = squareAround([0, 0], 5000);
    const r = recommend(aoi, 0);
    expect(r.algorithm).toBe("DIVIDE_BY_SQUARE");
    expect(gridSize(aoi)).toBe(500);
  });

  it("suggests buildings per task capped at 100", () => {
    expect(recommend(squareAround([0, 0], 1000), 50_000).params.num_buildings).toBe(100);
    expect(recommend(squareAround([0, 0], 1000), 667).params.num_buildings).toBe(10);
  });
});
