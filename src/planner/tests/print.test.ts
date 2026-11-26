import { describe, expect, it } from "vitest";
import { taskSheet, teamsSheet } from "../src/lib/print";
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
    comment: '<b>Chomba</b>, start "Monday"',
    feature_count: 12,
  },
};

describe("taskSheet", () => {
  it("lists the task details with the map, escaping user text", () => {
    const html = taskSheet(task, "data:image/png;base64,AAAA", "Kibera survey");
    expect(html).toContain("<title>Task 3 - Kibera survey</title>");
    expect(html).toContain("&lt;b&gt;Chomba&lt;/b&gt;");
    expect(html).not.toContain("<b>Chomba</b>");
    expect(html).toContain("start &quot;Monday&quot;");
    expect(html).toContain("<dd>12</dd>");
    expect(html).toContain('src="data:image/png;base64,AAAA"');
  });
});

describe("teamsSheet", () => {
  const hilly = { ...task, properties: { task_id: 4, assigned_group: "north", hilly: true } };
  const free = { ...task, properties: { task_id: 5 } };

  it("lists each team's tasks and hilly count", () => {
    const html = teamsSheet([task, hilly], "data:image/png;base64,AAAA", {}, "Bo city");
    expect(html).toContain("<title>Teams - Bo city</title>");
    expect(html).toContain("north</td><td>2</td><td>1</td><td>3, 4</td>");
  });

  it("adds a page per team with its highlighted map", () => {
    const html = teamsSheet([task, hilly, free], "data:overview", { north: "data:north" });
    expect(html).toContain('src="data:overview"');
    expect(html.match(/<section class="team">/g)).toHaveLength(1);
    expect(html).toContain("Team north</h2>");
    expect(html).toContain("<dt>Task numbers</dt><dd>3, 4</dd>");
    expect(html).toContain('src="data:north"');
  });
});
