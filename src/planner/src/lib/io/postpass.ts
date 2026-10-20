import type { FetchFn } from "./files";
import type { FeatureCollection } from "geojson";
import type { BBox } from "../geo";

export const POSTPASS_URL = "https://postpass.geofabrik.de/api/interpreter";

/** Fetch roads, waterways and railways (the split lines the SQL uses) inside a bbox. */
export async function fetchRoads(
  [w, s, e, n]: BBox,
  fetchFn: FetchFn = fetch,
): Promise<FeatureCollection> {
  if (![w, s, e, n].every(Number.isFinite)) throw new Error("Invalid bbox");
  const query = `SELECT osm_id, tags, geom FROM postpass_line
    WHERE (tags ? 'highway' OR tags ? 'waterway' OR tags ? 'railway')
    AND geom && ST_MakeEnvelope(${w}, ${s}, ${e}, ${n}, 4326)`;
  const res = await fetchFn(POSTPASS_URL, {
    method: "POST",
    body: new URLSearchParams({ data: query }),
  });
  if (!res.ok)
    throw new Error(`PostPass API error (HTTP ${res.status}). Try again later or upload roads.`);
  const { features } = (await res.json()) as FeatureCollection;
  return { type: "FeatureCollection", features };
}
