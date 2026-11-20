import { describe, expect, it } from "vitest";
import type { Position } from "geojson";
import { groupRoutes, type Segment } from "../src/lib/engine/routes";

const seg = (start: Position, end: Position, len = 100): Segment => ({
  start,
  end,
  mid: [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2],
  len,
});

describe("groupRoutes", () => {
  it("never groups streets that are close but not connected", () => {
    // Two parallel streets either side of a block, each a chain of two segments.
    const west = [seg([0, 2], [0, 1]), seg([0, 1], [0, 0])];
    const east = [seg([0.1, 2], [0.1, 1]), seg([0.1, 1], [0.1, 0])];
    const route = groupRoutes([...west, ...east], 200);
    expect(route[0]).toBe(route[1]);
    expect(route[2]).toBe(route[3]);
    expect(route[0]).not.toBe(route[2]);
  });

  it("grows routes to about the target length, starting in the north", () => {
    const chain = [0, 1, 2, 3, 4, 5].map((i) => seg([0, 6 - i], [0, 5 - i]));
    expect(groupRoutes(chain, 300)).toEqual([0, 0, 0, 1, 1, 1]);
  });

  it("merges a short leftover into a touching route", () => {
    const chain = [seg([0, 3], [0, 2]), seg([0, 2], [0, 1]), seg([0, 1], [0, 0], 50)];
    const route = groupRoutes(chain, 200);
    expect(new Set(route).size).toBe(1);
  });

  it("joins a short stub that touches nothing to the nearest route", () => {
    const street = [seg([0, 0.002], [0, 0.001]), seg([0, 0.001], [0, 0])];
    const farStreet = [seg([5, 2], [5, 1]), seg([5, 1], [5, 0])];
    const stub = seg([0.0005, 0.0005], [0.0006, 0.0005], 20);
    const route = groupRoutes([...street, ...farStreet, stub], 200);
    expect(route[4]).toBe(route[0]);
    expect(route[0]).not.toBe(route[2]);
  });

  it("keeps a stub separate when the nearest route is beyond the target length", () => {
    const street = [seg([0, 0.002], [0, 0.001]), seg([0, 0.001], [0, 0])];
    const stub = seg([0.01, 0.0005], [0.0101, 0.0005], 20);
    const route = groupRoutes([...street, stub], 200);
    expect(route[2]).not.toBe(route[0]);
  });
});
