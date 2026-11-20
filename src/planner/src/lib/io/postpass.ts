import type { FetchFn } from "./files";
import type { FeatureCollection } from "geojson";
import type { BBox } from "../geo";

export const POSTPASS_URL = "https://postpass.geofabrik.de/api/interpreter";
const DOWNLOAD_FAILED =
  "OSM roads could not be downloaded at this time. Please try again later, or upload your own roads in step 2.";
const MAX_BBOX_DEG2 = 0.05; // roughly 25 x 25 km near the equator

/** PostPass answers quickly for areas up to MAX_BBOX_DEG2. */
export const canFetchRoads = ([w, s, e, n]: BBox) => (e - w) * (n - s) <= MAX_BBOX_DEG2;

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
  }).catch(() => {
    throw new Error(DOWNLOAD_FAILED);
  });
  if (!res.ok) throw new Error(`${DOWNLOAD_FAILED} (HTTP ${res.status})`);
  const { features } = (await res.json()) as FeatureCollection;
  return { type: "FeatureCollection", features };
}
