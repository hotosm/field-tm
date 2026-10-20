import type {
  Feature,
  FeatureCollection,
  Geometry,
  MultiPolygon,
  Polygon,
  Position,
} from "geojson";

export type Area = Polygon | MultiPolygon;
export type BBox = [number, number, number, number];

function eachPosition(g: Geometry, fn: (p: Position) => void) {
  switch (g.type) {
    case "Point":
      fn(g.coordinates);
      break;
    case "MultiPoint":
    case "LineString":
      g.coordinates.forEach(fn);
      break;
    case "MultiLineString":
    case "Polygon":
      g.coordinates.flat().forEach(fn);
      break;
    case "MultiPolygon":
      g.coordinates.flat(2).forEach(fn);
      break;
    case "GeometryCollection":
      g.geometries.forEach((c) => eachPosition(c, fn));
      break;
  }
}

export function bbox(geoms: Geometry | Geometry[]): BBox {
  const b: BBox = [Infinity, Infinity, -Infinity, -Infinity];
  for (const g of [geoms].flat()) {
    eachPosition(g, ([x, y]) => {
      b[0] = Math.min(b[0], x);
      b[1] = Math.min(b[1], y);
      b[2] = Math.max(b[2], x);
      b[3] = Math.max(b[3], y);
    });
  }
  return b;
}

export function geometries(input: unknown): Geometry[] {
  const g = input as Geometry | Feature | FeatureCollection | null;
  if (!g || typeof g !== "object") return [];
  if (g.type === "FeatureCollection") return g.features.flatMap((f) => geometries(f));
  if (g.type === "Feature") return g.geometry ? [g.geometry] : [];
  if (g.type === "GeometryCollection") return g.geometries;
  return "coordinates" in g ? [g] : [];
}

/** Combine all polygons in any GeoJSON input into one area geometry. */
export function toArea(input: unknown): Area {
  const polys = geometries(input).flatMap((g) =>
    g.type === "Polygon" ? [g.coordinates] : g.type === "MultiPolygon" ? g.coordinates : [],
  );
  if (polys.length === 0) throw new Error("No polygon found in the area file");
  return polys.length === 1
    ? { type: "Polygon", coordinates: polys[0] }
    : { type: "MultiPolygon", coordinates: polys };
}

export function toFeatureCollection(input: unknown): FeatureCollection {
  const g = input as FeatureCollection | Feature | Geometry;
  if (g?.type === "FeatureCollection") return g;
  if (g?.type === "Feature") return { type: "FeatureCollection", features: [g] };
  if (g && "coordinates" in g)
    return {
      type: "FeatureCollection",
      features: [{ type: "Feature", geometry: g, properties: {} }],
    };
  throw new Error("Not valid GeoJSON");
}

const M_PER_DEG = 111_320;

/** Square of `sizeM` metres centred on a point. */
export function squareAround([lng, lat]: [number, number], sizeM: number): Polygon {
  const dy = sizeM / 2 / M_PER_DEG;
  const dx = dy / Math.cos((lat * Math.PI) / 180);
  return {
    type: "Polygon",
    coordinates: [
      [
        [lng - dx, lat - dy],
        [lng + dx, lat - dy],
        [lng + dx, lat + dy],
        [lng - dx, lat + dy],
        [lng - dx, lat - dy],
      ],
    ],
  };
}

/** Approximate area in square metres (equirectangular; fine for task-sized areas). */
export function areaM2(g: Area): number {
  const polys = g.type === "Polygon" ? [g.coordinates] : g.coordinates;
  const ringArea = (ring: Position[]) => {
    const k = Math.cos((ring[0][1] * Math.PI) / 180) * M_PER_DEG * M_PER_DEG;
    let s = 0;
    for (let i = 0; i < ring.length - 1; i++)
      s += ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1];
    return Math.abs(s / 2) * k;
  };
  return polys.reduce(
    (sum, rings) => sum + ringArea(rings[0]) - rings.slice(1).reduce((h, r) => h + ringArea(r), 0),
    0,
  );
}

/** A representative point: mean of a polygon's outer ring, a line's middle vertex, or the point. */
export function featurePoint(g: Geometry): Position | null {
  switch (g.type) {
    case "Point":
      return g.coordinates;
    case "MultiPoint":
      return g.coordinates[0] ?? null;
    case "LineString":
      return g.coordinates[Math.floor(g.coordinates.length / 2)] ?? null;
    case "MultiLineString":
      return g.coordinates[0]?.[Math.floor(g.coordinates[0].length / 2)] ?? null;
    case "Polygon":
    case "MultiPolygon": {
      const ring = g.type === "Polygon" ? g.coordinates[0] : g.coordinates[0]?.[0];
      if (!ring?.length) return null;
      const n = ring.length > 1 ? ring.length - 1 : 1; // skip the closing vertex
      let x = 0;
      let y = 0;
      for (let i = 0; i < n; i++) {
        x += ring[i][0];
        y += ring[i][1];
      }
      return [x / n, y / n];
    }
    default:
      return null;
  }
}
