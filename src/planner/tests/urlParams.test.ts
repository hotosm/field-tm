import { describe, expect, it } from "vitest";
import { parseMode } from "../src/lib/urlParams";
import { decodeTask, encodeTask, shareUrl } from "../src/lib/share";
import type { Task } from "../src/lib/taskPlan";

const t: Task = {
  type: "Feature",
  geometry: {
    type: "Polygon",
    coordinates: [
      [
        [85.123456789, 27.7],
        [85.2, 27.7],
        [85.2, 27.8],
        [85.123456789, 27.7],
      ],
    ],
  },
  properties: { task_id: 3, assigned_group: "team-a", comment: "Ñamaste ✓", feature_count: 9 },
};

describe("parseMode", () => {
  it("defaults to standalone", () => {
    expect(parseMode("")).toEqual({
      kind: "standalone",
      aoi: undefined,
      features: undefined,
      roads: undefined,
      returnTo: undefined,
    });
  });

  it("reads an absolute http(s) return_to and ignores anything else", () => {
    const back = "https://field.hotosm.org/projects/12";
    expect(parseMode(`?return_to=${encodeURIComponent(back)}`)).toMatchObject({ returnTo: back });
    expect(parseMode("?return_to=javascript:alert(1)")).toMatchObject({ returnTo: undefined });
    expect(parseMode("?return_to=/projects/12")).toMatchObject({ returnTo: undefined });
  });

  it("reads public GeoJSON urls and ignores unsafe schemes", () => {
    const m = parseMode(
      "?aoi=https://example.org/a.geojson&features=javascript:alert(1)&roads=data/r.geojson",
    );
    expect(m).toEqual({
      kind: "standalone",
      aoi: "https://example.org/a.geojson",
      features: undefined,
      roads: "data/r.geojson",
      returnTo: undefined,
    });
  });

  it("reads Field-TM project and viewer mode", () => {
    expect(parseMode("?project=12")).toEqual({ kind: "fieldtm", project: "12", view: false });
    expect(parseMode("?project=12&view=1")).toEqual({ kind: "fieldtm", project: "12", view: true });
    expect(parseMode("?project=../x").kind).toBe("standalone");
  });

  it("reads a shared task from the hash or query", () => {
    const enc = encodeTask(t);
    const m = parseMode("", `#task=${enc}`);
    expect(m.kind).toBe("task");
    expect(parseMode(`?task=${enc}`).kind).toBe("task");
    expect(parseMode("", "#task=garbage").kind).toBe("standalone");
  });
});

describe("share", () => {
  it("round-trips a task, rounding coordinates and dropping counts", () => {
    const back = decodeTask(encodeTask(t))!;
    expect(back.properties).toEqual({ task_id: 3, assigned_group: "team-a", comment: "Ñamaste ✓" });
    expect(back.geometry.coordinates[0][0]).toEqual([85.123457, 27.7]);
  });

  it("builds a link without the original query", () => {
    const url = shareUrl(t, "https://example.org/planner/?project=3#x");
    expect(url).toMatch(/^https:\/\/example\.org\/planner\/#task=[\w-]+$/);
  });

  it("rejects tampered payloads", () => {
    const bad = btoa(
      JSON.stringify({
        type: "Feature",
        geometry: { type: "Point", coordinates: [0, 0] },
        properties: {},
      }),
    );
    expect(decodeTask(bad)).toBeNull();
  });
});
