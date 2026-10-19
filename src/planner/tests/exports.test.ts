import { describe, expect, it } from "vitest";
import { taskGPX, taskGeoJSON, planGeoJSON } from "../src/lib/exports";
import { makePlan, type Task } from "../src/lib/taskPlan";

const t: Task = {
  type: "Feature",
  geometry: {
    type: "Polygon",
    coordinates: [
      [
        [85.3, 27.71],
        [85.31, 27.71],
        [85.31, 27.72],
        [85.3, 27.71],
      ],
    ],
  },
  properties: { task_id: 4, assigned_to: "Chomba & <co>", comment: 'Start "Monday"' },
};

describe("exports", () => {
  it("writes a GPX track of the task boundary with escaped text", () => {
    const gpx = taskGPX(t);
    expect(gpx).toContain('<gpx version="1.1"');
    expect(gpx).toContain("<name>Task 4 (Chomba &amp; &lt;co&gt;)</name>");
    expect(gpx).toContain("<desc>Start &quot;Monday&quot;</desc>");
    expect(gpx.match(/<trkpt /g)).toHaveLength(4);
    expect(gpx).toContain('<trkpt lat="27.71" lon="85.3"/>');
    expect(gpx).not.toMatch(/<(?!\/?(gpx|metadata|name|trk|desc|trkseg|trkpt|\?xml))\w/);
  });

  it("writes per-task and whole-plan GeoJSON", () => {
    expect(JSON.parse(taskGeoJSON(t)).features[0].properties.task_id).toBe(4);
    const plan = JSON.parse(
      planGeoJSON(makePlan([{ ...t, properties: { ...t.properties, task_id: 1 } }])),
    );
    expect(plan.task_plan_version).toBe(1);
  });
});
