import type { FeatureCollection, Geometry, Polygon, Position } from "geojson";
import { classify } from "./engine/splitter";
import { featurePoint } from "./geo";
import type { Task } from "./taskPlan";

export type Point = [number, number];

/** One point per feature to map (see classify). */
export function featurePoints(fc: FeatureCollection | null): Point[] {
  return classify(fc).polys.flatMap((p) => {
    const pt = featurePoint(p.g as Geometry);
    return pt ? [[pt[0], pt[1]] as Point] : [];
  });
}

function inRing([x, y]: Point, ring: Position[]): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

export function featuresInside(points: Point[], polygon: Polygon): number {
  const [outer, ...holes] = polygon.coordinates;
  let [x0, y0, x1, y1] = [Infinity, Infinity, -Infinity, -Infinity];
  for (const [x, y] of outer) {
    x0 = Math.min(x0, x);
    y0 = Math.min(y0, y);
    x1 = Math.max(x1, x);
    y1 = Math.max(y1, y);
  }
  let n = 0;
  for (const p of points) {
    if (p[0] < x0 || p[0] > x1 || p[1] < y0 || p[1] > y1) continue;
    if (inRing(p, outer) && !holes.some((h) => inRing(p, h))) n++;
  }
  return n;
}

/** Recount features in every task, e.g. after a manual edit. */
export function withFeatureCounts(tasks: Task[], points: Point[]): Task[] {
  return tasks.map((t) => ({
    ...t,
    properties: { ...t.properties, feature_count: featuresInside(points, t.geometry) },
  }));
}
