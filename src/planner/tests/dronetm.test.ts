import { describe, expect, it, vi } from "vitest";
import { getDroneTmProject } from "../src/lib/io/dronetm";

const square = (x: number) => ({
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

// Shaped like Drone-TM's public GET /projects/{id}, which nests outlines in Features.
const project = {
  name: "Wilberforce",
  outline: { type: "Feature", geometry: square(0), properties: {} },
  no_fly_zones: {
    type: "FeatureCollection",
    features: [{ type: "Feature", geometry: square(5), properties: {} }],
  },
  tasks: [
    {
      project_task_index: 2,
      outline: { type: "Feature", geometry: square(2), properties: {} },
      state: "LOCKED",
    },
    {
      project_task_index: 1,
      outline: { type: "Feature", geometry: square(1), properties: {} },
      state: null,
    },
  ],
};

const reply = (body: unknown) => vi.fn(async () => new Response(JSON.stringify(body)));

describe("getDroneTmProject", () => {
  it("keeps Drone-TM task numbers and no-fly zones", async () => {
    const f = reply(project);
    const input = await getDroneTmProject("https://api.example.org/projects/abc", f);
    expect(f).toHaveBeenCalledWith("https://api.example.org/projects/abc", undefined);
    expect(input.name).toBe("Wilberforce");
    expect(input.aoi).toEqual(square(0));
    expect(input.noFlyZones).toEqual(square(5));
    expect(input.plan.features.map((t) => [t.properties.task_id, t.geometry])).toEqual([
      [1, square(1)],
      [2, square(2)],
    ]);
  });

  it("allows projects without no-fly zones", async () => {
    const input = await getDroneTmProject("/p.json", reply({ ...project, no_fly_zones: null }));
    expect(input.noFlyZones).toBeNull();
  });

  it("rejects responses that aren't a project", async () => {
    await expect(getDroneTmProject("/p.json", reply({ detail: "Not found" }))).rejects.toThrow(
      "not a Drone-TM project",
    );
  });

  it("rejects task numbers with gaps", async () => {
    const tasks = [{ ...project.tasks[0], project_task_index: 3 }, project.tasks[1]];
    await expect(getDroneTmProject("/p.json", reply({ ...project, tasks }))).rejects.toThrow(
      "task_id values must be 1..n",
    );
  });
});
