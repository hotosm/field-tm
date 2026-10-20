// Straight skeleton via CGAL compiled to wasm (`straight-skeleton`), standing
// in for SFCGAL's CG_StraightSkeleton, which PGlite's PostGIS lacks.
import type { MultiLineString, Polygon } from "geojson";

type Builder = typeof import("straight-skeleton").SkeletonBuilder;
let builder: Promise<Builder> | null = null;

function load(): Promise<Builder> {
  return (builder ??= (async () => {
    // The wasm glue is built for browsers/workers only; let it run under Node (tests).
    const g = globalThis as Record<string, unknown>;
    const shim = typeof g.window === "undefined" && typeof g.importScripts === "undefined";
    if (shim) {
      g.self ??= globalThis;
      g.importScripts = () => {};
    }
    try {
      const mod = await import("straight-skeleton");
      const B = (mod.SkeletonBuilder ??
        (mod as unknown as { default: typeof mod }).default.SkeletonBuilder) as Builder;
      await B.init();
      return B;
    } finally {
      if (shim) delete g.importScripts;
    }
  })());
}

/**
 * Skeleton edges of each polygon (outer ring CCW, holes CW, closed rings),
 * excluding the input edges, like CG_StraightSkeleton. Null if CGAL fails.
 */
export async function straightSkeleton(polygons: Polygon[]): Promise<MultiLineString | null> {
  const B = await load();
  const lines: number[][][] = [];
  for (const poly of polygons) {
    // Work in a local, roughly metre-scaled frame for numerical robustness.
    const [x0, y0] = poly.coordinates[0][0];
    const k = 1e5;
    const rings = poly.coordinates.map((r) => r.map(([x, y]) => [(x - x0) * k, (y - y0) * k]));
    const sk = B.buildFromPolygon(rings);
    if (!sk) return null;
    const pt = (i: number) => [sk.vertices[i][0] / k + x0, sk.vertices[i][1] / k + y0];
    const seen = new Set<string>();
    for (const face of sk.polygons) {
      for (let j = 0; j < face.length; j++) {
        const a = face[j],
          b = face[(j + 1) % face.length];
        // Both ends at time 0 means an input edge.
        if (sk.vertices[a][2] === 0 && sk.vertices[b][2] === 0) continue;
        const key = a < b ? `${a},${b}` : `${b},${a}`;
        if (seen.has(key)) continue;
        seen.add(key);
        lines.push([pt(a), pt(b)]);
      }
    }
  }
  return { type: "MultiLineString", coordinates: lines };
}
