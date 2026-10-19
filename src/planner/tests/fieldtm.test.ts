import { describe, expect, it, vi } from "vitest";
import { ApiError, getPlannerInput, loginUrl, saveTaskPlan } from "../src/lib/io/fieldtm";
import { makePlan, type Task } from "../src/lib/taskPlan";

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
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
  properties: { task_id: 1 },
};

describe("Field-TM API adapter", () => {
  it("gets planner input from the same origin", async () => {
    const body = {
      project: { id: 5, name: "P", field_mapping_app: "ODK" },
      aoi: task.geometry,
      features: null,
      task_plan: null,
    };
    const f = vi.fn(async () => json(200, body));
    expect(await getPlannerInput(5, f)).toEqual(body);
    expect(f).toHaveBeenCalledWith("/api/v1/projects/5/planner-input", {
      credentials: "same-origin",
    });
  });

  it("PUTs a validated task plan", async () => {
    const f = vi.fn(async (_url: string, _init?: RequestInit) => json(200, { task_count: 1 }));
    expect(await saveTaskPlan(5, makePlan([task], "MANUAL"), f)).toEqual({ task_count: 1 });
    const [url, init] = f.mock.calls[0];
    expect(url).toBe("/api/v1/projects/5/task-plan");
    expect(init).toMatchObject({
      method: "PUT",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
    });
    expect(JSON.parse(String(init!.body)).task_plan_version).toBe(1);
  });

  it("refuses to send an invalid plan", async () => {
    const f = vi.fn();
    await expect(saveTaskPlan(5, makePlan([]), f)).rejects.toThrow(/no tasks/);
    expect(f).not.toHaveBeenCalled();
  });

  it.each([
    [401, true, /log in/i],
    [403, true, /project manager/],
    [404, false, /not found/],
    [422, false, /bad geometry/],
  ])("maps HTTP %i to a clear error", async (status, isAuth, msg) => {
    const err = await getPlannerInput(1, async () =>
      json(status, { detail: "bad geometry" }),
    ).catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.isAuth).toBe(isAuth);
    expect(err.message).toMatch(msg);
  });

  it("builds a login link that returns here", () => {
    expect(loginUrl("/planner/?project=5")).toBe("/login?return_to=%2Fplanner%2F%3Fproject%3D5");
  });
});
