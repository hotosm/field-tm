import type { FetchFn } from "./files";
import type { FeatureCollection } from "geojson";
import type { BBox } from "../geo";

export const OVERPASS_URL = "https://overpass-api.de/api/interpreter";

interface Way {
  type: "way";
  id: number;
  tags?: Record<string, string>;
  geometry?: { lat: number; lon: number }[];
}

/** Fetch roads, waterways and railways (the split lines the SQL uses) inside a bbox. */
export async function fetchRoads(
  [w, s, e, n]: BBox,
  fetchFn: FetchFn = fetch,
): Promise<FeatureCollection> {
  const b = `${s},${w},${n},${e}`;
  const query = `[out:json][timeout:60];(way["highway"](${b});way["waterway"](${b});way["railway"](${b}););out tags geom;`;
  const res = await fetchFn(OVERPASS_URL, {
    method: "POST",
    body: new URLSearchParams({ data: query }),
  });
  if (!res.ok)
    throw new Error(`Overpass API error (HTTP ${res.status}). Try again later or upload roads.`);
  const { elements } = (await res.json()) as { elements: Way[] };
  return {
    type: "FeatureCollection",
    features: elements
      .filter((el) => el.type === "way" && (el.geometry?.length ?? 0) > 1)
      .map((el) => ({
        type: "Feature",
        properties: { osm_id: el.id, tags: el.tags ?? {} },
        geometry: { type: "LineString", coordinates: el.geometry!.map((p) => [p.lon, p.lat]) },
      })),
  };
}
