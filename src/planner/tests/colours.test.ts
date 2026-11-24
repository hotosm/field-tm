import { describe, expect, it } from "vitest";
import { groupColour, legend, mapColour, taskColour, UNASSIGNED } from "../src/lib/colours";
import type { Task } from "../src/lib/taskPlan";

const task = (task_id: number, props: Partial<Task["properties"]> = {}): Task => ({
  type: "Feature",
  geometry: {
    type: "Polygon",
    coordinates: [
      [
        [0, 0],
        [1, 0],
        [1, 1],
        [0, 0],
      ],
    ],
  },
  properties: { task_id, ...props },
});

describe("legend", () => {
  it("labels by team and uses the map colour", () => {
    const items = legend([
      task(1, { assigned_group: "team-a", colour: "#123456" }),
      task(2, { assigned_group: "team-b" }),
      task(3),
    ]);
    expect(items.map((i) => [i.group, i.count])).toEqual([
      ["", 1],
      ["team-a", 1],
      ["team-b", 1],
    ]);
    expect(items.find((i) => i.group === "team-a")?.colour).toBe("#123456");
    expect(items.find((i) => i.group === "")?.colour).toBe(UNASSIGNED);
  });

  it("counts hilly tasks per team", () => {
    const items = legend([
      task(1, { assigned_group: "a", hilly: true }),
      task(2, { assigned_group: "a" }),
    ]);
    expect(items).toEqual([{ group: "a", colour: groupColour("a"), count: 2, hilly: 1 }]);
  });

  it("matches taskColour for each task", () => {
    const t = task(1, { assigned_group: "north" });
    expect(legend([t])[0].colour).toBe(taskColour(t));
  });
});

describe("mapColour", () => {
  const route = (task_id: number, props: Partial<Task["properties"]> = {}): Task => ({
    type: "Feature",
    geometry: {
      type: "MultiLineString",
      coordinates: [
        [
          [0, 0],
          [1, 0],
        ],
      ],
    },
    properties: { task_id, ...props },
  });

  it("gives neighbouring unassigned routes different colours", () => {
    expect(mapColour(route(1))).not.toBe(mapColour(route(2)));
    expect(mapColour(route(1))).not.toBe(UNASSIGNED);
  });

  it("uses the team colour once a route is assigned, and leaves areas alone", () => {
    expect(mapColour(route(1, { assigned_group: "north" }))).toBe(
      taskColour(route(1, { assigned_group: "north" })),
    );
    expect(mapColour(task(1))).toBe(UNASSIGNED);
  });
});
