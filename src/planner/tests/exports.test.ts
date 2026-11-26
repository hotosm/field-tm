import { describe, expect, it } from "vitest";
import { aoiGPX, aoiGeoJSON, taskGPX, taskGeoJSON, planGeoJSON } from "../src/lib/exports";
import type { Area } from "../src/lib/geo";
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
  properties: { task_id: 4, assigned_group: "team-a", comment: 'Chomba & <co>, start "Monday"' },
};

describe("exports", () => {
  it("writes a GPX track of the task boundary with escaped text", () => {
    const gpx = taskGPX(t);
    expect(gpx).toContain('<gpx version="1.1"');
    expect(gpx).toContain("<name>Task 4 (team-a)</name>");
    expect(gpx).toContain("<desc>Chomba &amp; &lt;co&gt;, start &quot;Monday&quot;</desc>");
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

  it("writes the area as GeoJSON and GPX, for Polygon and MultiPolygon", () => {
    const ring = [
      [85.3, 27.71],
      [85.31, 27.71],
      [85.31, 27.72],
      [85.3, 27.71],
    ];
    const poly: Area = { type: "Polygon", coordinates: [ring] };
    const multi: Area = { type: "MultiPolygon", coordinates: [[ring], [ring, ring]] };

    const fc = JSON.parse(aoiGeoJSON(poly));
    expect(fc.features).toHaveLength(1);
    expect(fc.features[0].geometry).toEqual(poly);
    expect(JSON.parse(aoiGeoJSON(multi)).features[0].geometry.type).toBe("MultiPolygon");

    expect(aoiGPX(poly).match(/<trkseg>/g)).toHaveLength(1);
    expect(aoiGPX(poly)).toContain('<trkpt lat="27.71" lon="85.3"/>');
    expect(aoiGPX(multi).match(/<trkseg>/g)).toHaveLength(3);
  });

  it("writes no track segments for an area with no rings", () => {
    const empty: Area = { type: "Polygon", coordinates: [] };
    const gpx = aoiGPX(empty);
    expect(gpx).not.toContain("<trkseg>");
    expect(gpx).toContain("<name>Area of interest</name>");
    expect(JSON.parse(aoiGeoJSON(empty)).features[0].geometry.coordinates).toEqual([]);
  });
});
