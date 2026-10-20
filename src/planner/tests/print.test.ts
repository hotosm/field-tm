import { describe, expect, it } from "vitest";
import { taskSheet } from "../src/lib/print";
import type { Task } from "../src/lib/taskPlan";

const task: Task = {
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
  properties: {
    task_id: 3,
    assigned_group: "north",
    assigned_to: "<b>Chomba</b>",
    comment: 'Start "Monday"',
    feature_count: 12,
  },
};

describe("taskSheet", () => {
  it("lists the task details with the map, escaping user text", () => {
    const html = taskSheet(task, "data:image/png;base64,AAAA", "Kibera survey");
    expect(html).toContain("<title>Task 3 - Kibera survey</title>");
    expect(html).toContain("&lt;b&gt;Chomba&lt;/b&gt;");
    expect(html).not.toContain("<b>Chomba</b>");
    expect(html).toContain("Start &quot;Monday&quot;");
    expect(html).toContain("<dd>12</dd>");
    expect(html).toContain('src="data:image/png;base64,AAAA"');
  });
});
