/**
 * Group street segments (split at junctions) into connected routes.
 *
 * Each route grows from the northernmost free segment, adding the connected
 * segment nearest that start until it reaches the target length. Routes only
 * spread along the network, so they never jump a block, river or railway. The
 * exception is a short isolated stub, which joins a route within a route length.
 */
import type { Position } from "geojson";

export interface Segment {
  start: Position;
  end: Position;
  mid: Position;
  len: number;
}

const METRES_PER_DEGREE = 111_320;

const key = ([x, y]: Position) => `${x.toFixed(7)},${y.toFixed(7)}`;
const dist2 = (a: Position, b: Position) => (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2;

/** Segments sharing a junction with each segment. */
function neighbours(segs: Segment[]): number[][] {
  const atJunction = new Map<string, number[]>();
  segs.forEach((s, i) => {
    for (const k of new Set([key(s.start), key(s.end)])) {
      atJunction.set(k, [...(atJunction.get(k) ?? []), i]);
    }
  });
  return segs.map((s, i) =>
    [...new Set([...atJunction.get(key(s.start))!, ...atJunction.get(key(s.end))!])].filter(
      (j) => j !== i,
    ),
  );
}

/** Route number for each segment. Short leftover routes join a touching route. */
export function groupRoutes(segs: Segment[], target: number): number[] {
  const near = neighbours(segs);
  const route = segs.map(() => -1);
  const lengths: number[] = [];
  const north = segs.map((_, i) => i);
  north.sort((a, b) => segs[b].mid[1] - segs[a].mid[1] || segs[a].mid[0] - segs[b].mid[0]);

  for (const seed of north) {
    if (route[seed] !== -1) continue;
    const id = lengths.length;
    const frontier = new Set<number>([seed]);
    let len = 0;
    while (len < target && frontier.size) {
      const next = [...frontier].reduce((a, b) =>
        dist2(segs[a].mid, segs[seed].mid) <= dist2(segs[b].mid, segs[seed].mid) ? a : b,
      );
      frontier.delete(next);
      route[next] = id;
      len += segs[next].len;
      for (const j of near[next]) if (route[j] === -1) frontier.add(j);
    }
    lengths.push(len);
  }

  // A short stub with nothing touching it (e.g. clipped at the area edge) joins the
  // nearest route, unless that is further than a route length (e.g. across a river).
  const maxGap2 = (target / METRES_PER_DEGREE) ** 2;
  const nearest = (members: number[]) => {
    const others = segs.flatMap((_, j) => (members.includes(j) ? [] : [j]));
    if (!others.length) return -1;
    const gap = (j: number) => Math.min(...members.map((i) => dist2(segs[i].mid, segs[j].mid)));
    const closest = others.reduce((a, b) => (gap(a) <= gap(b) ? a : b));
    return gap(closest) <= maxGap2 ? route[closest] : -1;
  };

  lengths.forEach((len, id) => {
    if (len >= target / 2) return;
    const members = route.flatMap((r, i) => (r === id ? [i] : []));
    if (!members.length) return;
    const touching = members.flatMap((i) => near[i].map((j) => route[j])).filter((r) => r !== id);
    const into = touching.length
      ? touching.reduce((a, b) => (lengths[a] <= lengths[b] ? a : b))
      : nearest(members);
    if (into === -1) return;
    for (const i of members) route[i] = into;
    lengths[into] += len;
    lengths[id] = 0;
  });
  return route;
}
