import { describe, expect, it, vi } from "vitest";
import { bbox } from "../src/lib/geo";
import { withSlopes } from "../src/lib/io/terrain";
import type { Task } from "../src/lib/taskPlan";

const area = (task_id: number, slope_deg?: number): Task => ({
  type: "Feature",
  geometry: {
    type: "Polygon",
    coordinates: [
      [
        [-13.2, 8.4],
        [-13.1, 8.4],
        [-13.1, 8.5],
        [-13.2, 8.4],
      ],
    ],
  },
  properties: { task_id, ...(slope_deg === undefined ? {} : { slope_deg }) },
});
const route: Task = {
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
  properties: { task_id: 9 },
};

/** Replies with one mean per posted feature, from `means` in order. */
function statistics(means: (number | null)[]) {
  let next = 0;
  return vi.fn(async (_url: string, init?: RequestInit) => {
    const { features } = JSON.parse(init!.body as string);
    const reply = features.map(() => ({
      properties: { statistics: { b1: { mean: means[next++] } } },
    }));
    return new Response(JSON.stringify({ features: reply }));
  });
}

describe("withSlopes", () => {
  it("adds rounded slopes to unscored area tasks only", async () => {
    const f = statistics([12.34]);
    const out = await withSlopes([area(1, 3), area(2), route], undefined, f);
    expect(out.map((t) => t.properties.slope_deg)).toEqual([3, 12.3, undefined]);
    expect(f).toHaveBeenCalledTimes(1);
    const url = new URL(f.mock.calls[0][0]);
    expect(url.searchParams.get("algorithm")).toBe("slope");
    expect(url.searchParams.get("dst_crs")).toBe("EPSG:3857");
  });

  it("sends large plans in chunks", async () => {
    const tasks = Array.from({ length: 120 }, (_, i) => area(i + 1));
    const f = statistics(tasks.map((_, i) => i));
    const out = await withSlopes(tasks, undefined, f);
    expect(f).toHaveBeenCalledTimes(3);
    expect(out[119].properties.slope_deg).toBe(119);
  });

  it("scores tiny tasks on a larger square around them", async () => {
    const tiny: Task = {
      ...area(1),
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [-13.2, 8.4],
            [-13.1999, 8.4],
            [-13.1999, 8.4001],
            [-13.2, 8.4],
          ],
        ],
      },
    };
    const f = statistics([4]);
    await withSlopes([tiny], undefined, f);
    const [sent] = JSON.parse(f.mock.calls[0][1]!.body as string).features;
    const [west, , east] = bbox(sent.geometry);
    expect((east - west) * 111_320 * Math.cos((8.4 * Math.PI) / 180)).toBeCloseTo(60, 0);
  });

  it("skips tasks without DEM data", async () => {
    const out = await withSlopes([area(1)], undefined, statistics([null]));
    expect(out[0].properties.slope_deg).toBeUndefined();
  });

  it("does nothing when every task is scored", async () => {
    const f = statistics([]);
    const tasks = [area(1, 5)];
    expect(await withSlopes(tasks, undefined, f)).toBe(tasks);
    expect(f).not.toHaveBeenCalled();
  });

  it("fails on an HTTP error", async () => {
    const f = vi.fn(async () => new Response("", { status: 503 }));
    await expect(withSlopes([area(1)], undefined, f)).rejects.toThrow("HTTP 503");
  });
});
