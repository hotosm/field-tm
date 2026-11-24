import { describe, expect, it } from "vitest";
import { PALETTE } from "../src/lib/colours";
import {
  divideAmongTeams,
  FLAT_SLOPE_DEG,
  hillyIds,
  MAX_TEAMS,
  TEAM_NAMES,
} from "../src/lib/teams";
import type { Task } from "../src/lib/taskPlan";

const square = (task_id: number, x: number, y: number, slope_deg?: number): Task => ({
  type: "Feature",
  geometry: {
    type: "Polygon",
    coordinates: [
      [
        [x, y],
        [x + 1, y],
        [x + 1, y + 1],
        [x, y + 1],
        [x, y],
      ],
    ],
  },
  properties: { task_id, ...(slope_deg === undefined ? {} : { slope_deg }) },
});

/** A `size` x `size` grid, hills on the left half. */
function grid(size: number): Task[] {
  return Array.from({ length: size * size }, (_, i) => {
    const x = i % size;
    const y = Math.floor(i / size);
    return square(i + 1, x, y, x < size / 2 ? 20 : 1);
  });
}

const teamOf = (tasks: Task[]) => tasks.map((t) => t.properties.assigned_group);
const count = <T>(items: T[], item: T) => items.filter((i) => i === item).length;

/** Number of groups of edge-sharing squares in each team. Corners don't count. */
function clusters(tasks: Task[]): number[] {
  const corner = (t: Task) => t.geometry.coordinates[0][0] as number[];
  const touches = (a: Task, b: Task) =>
    Math.abs(corner(a)[0] - corner(b)[0]) + Math.abs(corner(a)[1] - corner(b)[1]) === 1;
  return TEAM_NAMES.filter((name) => teamOf(tasks).includes(name)).map((name) => {
    const left = tasks.filter((t) => t.properties.assigned_group === name);
    let groups = 0;
    while (left.length) {
      groups++;
      const queue = left.splice(0, 1);
      while (queue.length) {
        const t = queue.pop()!;
        for (let i = left.length - 1; i >= 0; i--) {
          if (touches(t, left[i])) queue.push(...left.splice(i, 1));
        }
      }
    }
    return groups;
  });
}

/** Deterministic pseudo-random slopes between 0 and 30 degrees. */
const slopeAt = (i: number) => ((i * 7919) % 31) * 1.0;

describe("hillyIds", () => {
  it("marks tasks at or above the median slope", () => {
    const tasks = [10, 20, 30, 40].map((s, i) => square(i + 1, i, 0, s));
    expect([...hillyIds(tasks)]).toEqual([3, 4]);
  });

  it("treats gentle ground as flat, even above the median", () => {
    const gentle = FLAT_SLOPE_DEG - 1;
    const tasks = [1, 2, gentle, gentle].map((s, i) => square(i + 1, i, 0, s));
    expect(hillyIds(tasks).size).toBe(0);
  });

  it("treats tasks without a slope as flat", () => {
    expect(hillyIds([square(1, 0, 0), square(2, 1, 0)]).size).toBe(0);
  });
});

describe("divideAmongTeams", () => {
  it("names and colours teams, and marks hilly tasks", () => {
    const out = divideAmongTeams(grid(4), 2);
    expect(new Set(teamOf(out))).toEqual(new Set(["alpha", "bravo"]));
    const alpha = out.find((t) => t.properties.assigned_group === "alpha")!;
    expect(alpha.properties.colour).toBe(PALETTE[0]);
    expect(out.filter((t) => t.properties.hilly)).toHaveLength(8);
  });

  it("gives every team an equal share of hilly and flat tasks", () => {
    const out = divideAmongTeams(grid(6), 3);
    for (const name of TEAM_NAMES.slice(0, 3)) {
      const team = out.filter((t) => t.properties.assigned_group === name);
      expect(team).toHaveLength(12);
      expect(team.filter((t) => t.properties.hilly)).toHaveLength(6);
    }
  });

  it("keeps team totals within one when tasks don't divide evenly", () => {
    const tasks = grid(6).slice(0, 27);
    const teams = teamOf(divideAmongTeams(tasks, 4));
    const sizes = TEAM_NAMES.slice(0, 4).map((name) => count(teams, name));
    expect(sizes.reduce((a, b) => a + b)).toBe(27);
    expect(Math.max(...sizes) - Math.min(...sizes)).toBeLessThanOrEqual(1);
  });

  it("keeps each team's flat tasks close together", () => {
    const flat = Array.from({ length: 64 }, (_, i) => square(i + 1, i % 8, Math.floor(i / 8), 0));
    const out = divideAmongTeams(flat, 4);
    for (const name of TEAM_NAMES.slice(0, 4)) {
      const corners = out
        .filter((t) => t.properties.assigned_group === name)
        .map((t) => t.geometry.coordinates[0][0] as number[]);
      const xs = corners.map(([x]) => x);
      const ys = corners.map(([, y]) => y);
      // A Hilbert curve cuts an 8x8 grid into four 4x4 quadrants.
      expect(Math.max(...xs) - Math.min(...xs)).toBe(3);
      expect(Math.max(...ys) - Math.min(...ys)).toBe(3);
    }
  });

  it("gives each team at most two connected clusters on mixed terrain", () => {
    const tasks = grid(12).map((t, i) => ({
      ...t,
      properties: { ...t.properties, slope_deg: slopeAt(i) },
    }));
    const out = divideAmongTeams(tasks, 5);
    expect(Math.max(...clusters(out))).toBeLessThanOrEqual(2);
  });

  it("keeps clusters connected on a ragged area", () => {
    // A diagonal band, which the Hilbert curve keeps leaving and re-entering.
    const tasks = grid(12)
      .filter((t) => {
        const [x, y] = t.geometry.coordinates[0][0] as number[];
        return Math.abs(x - y) <= 3;
      })
      .map((t, i) => ({
        ...t,
        properties: { ...t.properties, task_id: i + 1, slope_deg: slopeAt(i) },
      }));
    const out = divideAmongTeams(tasks, 5);
    expect(Math.max(...clusters(out))).toBeLessThanOrEqual(2);
  });

  it("gives each team one cluster without terrain", () => {
    const flat = Array.from({ length: 100 }, (_, i) => square(i + 1, i % 10, Math.floor(i / 10)));
    expect(clusters(divideAmongTeams(flat, 3))).toEqual([1, 1, 1]);
  });

  it("keeps teams even and in one piece where the area has a gap", () => {
    const notched = Array.from({ length: 144 }, (_, i) => [i % 12, Math.floor(i / 12)])
      .filter(([x, y]) => !(x >= 3 && x <= 8 && y >= 4 && y <= 7))
      .map(([x, y], i) => square(i + 1, x, y));
    const out = divideAmongTeams(notched, 6);
    const sizes = TEAM_NAMES.slice(0, 6).map((name) => count(teamOf(out), name));
    expect(Math.max(...sizes) - Math.min(...sizes)).toBeLessThanOrEqual(1);
    expect(clusters(out)).toEqual([1, 1, 1, 1, 1, 1]);
  });

  it("limits teams to the palette and the number of tasks", () => {
    expect(new Set(teamOf(divideAmongTeams(grid(2), 10))).size).toBe(4);
    expect(new Set(teamOf(divideAmongTeams(grid(6), 50))).size).toBe(MAX_TEAMS);
  });

  it("rounds fractional team counts down, so every task gets a team", () => {
    const out = divideAmongTeams(grid(2).concat(square(5, 2, 0, 1)), 2.5);
    expect(new Set(teamOf(out))).toEqual(new Set(["alpha", "bravo"]));
  });

  it("keeps task order and other properties", () => {
    const tasks = grid(2).map((t) => ({
      ...t,
      properties: { ...t.properties, comment: "Bring water" },
    }));
    const out = divideAmongTeams(tasks, 2);
    expect(out.map((t) => t.properties.task_id)).toEqual([1, 2, 3, 4]);
    expect(out.every((t) => t.properties.comment === "Bring water")).toBe(true);
  });
});
