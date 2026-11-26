import { PALETTE } from "./colours";
import type { Position } from "geojson";
import { featurePoint } from "./geo";
import { isAreaTask, type Task } from "./taskPlan";

export const TEAM_NAMES = [
  "alpha",
  "bravo",
  "charlie",
  "delta",
  "echo",
  "foxtrot",
  "golf",
  "hotel",
  "india",
  "juliet",
];
/** One palette colour per team. */
export const MAX_TEAMS = Math.min(TEAM_NAMES.length, PALETTE.length);
/**
 * Mean slope below which a task counts as flat, whatever the median. GLO-30
 * includes buildings and trees, so flat towns still average 4-6 degrees.
 */
export const FLAT_SLOPE_DEG = 10;
const HILBERT_ORDER = 16;

/** Position of (x, y) along a Hilbert curve filling a 2^order grid. */
function hilbertIndex(x: number, y: number, order = HILBERT_ORDER): number {
  let d = 0;
  for (let s = 2 ** (order - 1); s >= 1; s /= 2) {
    const rx = x & s ? 1 : 0;
    const ry = y & s ? 1 : 0;
    d += s * s * ((3 * rx) ^ ry);
    if (!ry) {
      if (rx) [x, y] = [s - 1 - x, s - 1 - y];
      [x, y] = [y, x];
    }
  }
  return d;
}

/** Tasks ordered so neighbours on the map are neighbours in the list. */
function spatialOrder(tasks: Task[]): Task[] {
  const points = tasks.map((t) => featurePoint(t.geometry) ?? [0, 0]);
  const xs = points.map((p) => p[0]);
  const ys = points.map((p) => p[1]);
  const [minX, minY] = [Math.min(...xs), Math.min(...ys)];
  const span = Math.max(Math.max(...xs) - minX, Math.max(...ys) - minY) || 1;
  const cells = 2 ** HILBERT_ORDER - 1;
  const index = points.map(([x, y]) =>
    hilbertIndex(Math.round(((x - minX) / span) * cells), Math.round(((y - minY) / span) * cells)),
  );
  return tasks
    .map((t, i) => ({ t, d: index[i] }))
    .sort((a, b) => a.d - b.d)
    .map((e) => e.t);
}

/** Split `count` into `n` sizes differing by at most one, larger first. */
const evenSizes = (count: number, n: number) =>
  Array.from({ length: n }, (_, i) => Math.floor(count / n) + (i < count % n ? 1 : 0));

function median(values: number[]): number {
  const s = [...values].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

/** Steeper than the median and FLAT_SLOPE_DEG. Tasks without a slope are flat. */
export function hillyIds(tasks: Task[]): Set<number> {
  const slopes = tasks
    .map((t) => t.properties.slope_deg)
    .filter((s): s is number => s !== undefined);
  if (!slopes.length) return new Set();
  const threshold = Math.max(median(slopes), FLAT_SLOPE_DEG);
  return new Set(
    tasks
      .filter((t) => (t.properties.slope_deg ?? 0) >= threshold)
      .map((t) => t.properties.task_id),
  );
}

/** About 1 cm in degrees: points closer than this to a line lie on it. */
const ON_LINE_DEG = 1e-7;

/** Whether segments a-b and c-d overlap along a stretch, not just at a point. */
function overlaps([ax, ay]: Position, [bx, by]: Position, [cx, cy]: Position, [dx, dy]: Position) {
  const length = Math.hypot(bx - ax, by - ay);
  if (!length) return false;
  const offset = (x: number, y: number) =>
    Math.abs((bx - ax) * (y - ay) - (by - ay) * (x - ax)) / length;
  if (offset(cx, cy) > ON_LINE_DEG || offset(dx, dy) > ON_LINE_DEG) return false;
  const along = (x: number, y: number) => ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / length;
  const [start, end] = [along(cx, cy), along(dx, dy)].sort((m, n) => m - n);
  return Math.min(length, end) - Math.max(0, start) > ON_LINE_DEG;
}

const segments = (t: Task) =>
  t.geometry.coordinates.flatMap((ring) => ring.slice(1).map((p, i) => [ring[i], p]));

/** Area tasks must share part of an edge, not only a corner. Routes may just meet. */
function sharesEdge(a: Task, b: Task): boolean {
  if (!isAreaTask(a) || !isAreaTask(b)) return true;
  const other = segments(b);
  return segments(a).some(([p, q]) => other.some(([r, s]) => overlaps(p, q, r, s)));
}

/** For each task, the indexes of touching tasks, found through shared vertices. */
function neighbours(tasks: Task[]): number[][] {
  const byVertex = new Map<string, number[]>();
  tasks.forEach((t, i) => {
    for (const [x, y] of t.geometry.coordinates.flat()) {
      const key = `${x.toFixed(7)},${y.toFixed(7)}`;
      byVertex.set(key, [...(byVertex.get(key) ?? []), i]);
    }
  });
  const candidates = tasks.map(() => new Set<number>());
  for (const shared of byVertex.values()) {
    for (const i of shared) {
      for (const j of shared) if (i !== j) candidates[i].add(j);
    }
  }
  return candidates.map((set, i) => [...set].filter((j) => sharesEdge(tasks[i], tasks[j])));
}

/**
 * Cut spatially ordered tasks into runs of about the given sizes. Each run grows
 * through touching tasks, earliest in the order first. A pick that would cut
 * off free tasks takes them too, so the free tasks stay in one group and every
 * run stays connected. Where that would overfill the run, the task that cuts
 * off least is taken instead.
 */
function connectedRuns(touching: number[][], sizes: number[]): number[] {
  const run: number[] = touching.map(() => -1);

  /** Free tasks that taking `pick` would separate from the largest free group. */
  const cutOff = (pick: number): number[] => {
    const free = touching[pick].filter((j) => run[j] === -1);
    const seen = new Set([pick]);
    const groups: number[][] = [];
    for (const start of free) {
      if (seen.has(start)) continue;
      seen.add(start);
      const group = [start];
      for (let k = 0; k < group.length; k++) {
        // Searching outward, the neighbours usually meet within a few steps.
        if (!groups.length && free.every((j) => seen.has(j))) return [];
        for (const j of touching[group[k]]) {
          if (run[j] !== -1 || seen.has(j)) continue;
          seen.add(j);
          group.push(j);
        }
      }
      groups.push(group);
    }
    return groups
      .sort((a, b) => b.length - a.length)
      .slice(1)
      .flat();
  };

  sizes.forEach((size, r) => {
    const frontier = new Set<number>();
    let taken = 0;
    const take = (i: number) => {
      run[i] = r;
      taken++;
      frontier.delete(i);
      touching[i].filter((j) => run[j] === -1).forEach((j) => frontier.add(j));
    };
    while (taken < size) {
      let pick = frontier.size ? Math.min(...frontier) : run.indexOf(-1);
      if (pick === -1) return;
      let lost = cutOff(pick);
      // Rarely, the next task splits off more than this run has room for.
      // Then look for the task that cuts off least.
      const room = size - taken - 1;
      for (const i of [...frontier].sort((a, b) => a - b)) {
        if (lost.length <= room) break;
        const alsoLost = cutOff(i);
        if (alsoLost.length < lost.length) [pick, lost] = [i, alsoLost];
      }
      take(pick);
      lost.forEach(take);
    }
  });
  return run;
}

/**
 * The team owning each run. With terrain, there are two runs per team and team
 * i gets the i-th hilliest and i-th flattest, measured on plain Hilbert runs.
 */
function runOwners(ordered: Task[], hilly: Set<number>, n: number): number[] {
  if (!hilly.size) return Array.from({ length: n }, (_, i) => i);
  let start = 0;
  const hillyCounts = evenSizes(ordered.length, 2 * n).map((size) => {
    const run = ordered.slice(start, (start += size));
    return run.filter((t) => hilly.has(t.properties.task_id)).length;
  });
  const hilliestFirst = hillyCounts
    .map((count, r) => ({ count, r }))
    .sort((a, b) => b.count - a.count)
    .map((e) => e.r);
  const owners: number[] = [];
  hilliestFirst.forEach((r, rank) => (owners[r] = Math.min(rank, 2 * n - 1 - rank)));
  return owners;
}

/**
 * Give each team at most two connected clusters along a Hilbert curve, paired
 * to balance hilly ground. Team totals differ by one, or by a few where a
 * team takes in a pocket of tasks that would otherwise be cut off.
 */
export function divideAmongTeams(tasks: Task[], teams: number): Task[] {
  const n = Math.max(1, Math.min(Math.floor(teams), MAX_TEAMS, tasks.length));
  const hilly = hillyIds(tasks);
  const ordered = spatialOrder(tasks);
  const owners = runOwners(ordered, hilly, n);
  const totals = evenSizes(tasks.length, n);
  const runsPerTeam = owners.length / n;
  const runSizes = owners.map((team, r) => {
    const nth = owners.slice(0, r).filter((o) => o === team).length;
    return evenSizes(totals[team], runsPerTeam)[nth];
  });
  const touching = neighbours(ordered);
  const owner = connectedRuns(touching, runSizes).map((run) => owners[run]);
  const team = new Map(ordered.map((t, i) => [t.properties.task_id, owner[i]]));

  return tasks.map((t) => {
    const i = team.get(t.properties.task_id)!;
    const properties = {
      ...t.properties,
      assigned_group: TEAM_NAMES[i],
      colour: PALETTE[i],
      hilly: hilly.has(t.properties.task_id),
    };
    return { ...t, properties };
  });
}
