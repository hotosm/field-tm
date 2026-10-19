import { describe, expect, it } from "vitest";
import { legend, taskColour, UNASSIGNED } from "../src/lib/colours";
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
  it("labels by team, then assignee, and uses the map colour", () => {
    const items = legend([
      task(1, { assigned_group: "team-a", colour: "#123456" }),
      task(2, { assigned_to: "Chomba" }),
      task(3),
    ]);
    expect(items.map((i) => [i.group, i.count])).toEqual([
      ["", 1],
      ["Chomba", 1],
      ["team-a", 1],
    ]);
    expect(items.find((i) => i.group === "team-a")?.colour).toBe("#123456");
    expect(items.find((i) => i.group === "")?.colour).toBe(UNASSIGNED);
  });

  it("matches taskColour for each task", () => {
    const t = task(1, { assigned_group: "north" });
    expect(legend([t])[0].colour).toBe(taskColour(t));
  });
});
