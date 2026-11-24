import type { Polygon } from "geojson";
import { bbox, M_PER_DEG, squareAround } from "../geo";
import { isAreaTask, type AreaTask, type Task } from "../taskPlan";
import type { FetchFn } from "./files";

const STATISTICS_URL =
  "https://api.imagery.hotosm.org/raster/collections/cop-dem-glo-30/statistics";
const TASKS_PER_REQUEST = 50;
/** Browsers run about six requests per host at once. */
const PARALLEL_REQUESTS = 6;
/** TiTiler fails on under ~2 DEM pixels (30 m each), so score tiny tasks on their surroundings. */
const MIN_SAMPLE_M = 60;

/**
 * Slope must be computed on a metric grid, so we use Web Mercator and correct
 * its 1/cos(lat) stretch with z_exaggeration. Buffer 0 avoids a TiTiler shape
 * mismatch between the slope output and each task's mask.
 */
function statisticsUrl(lat: number): string {
  const params = { buffer: 0, z_exaggeration: 1 / Math.cos((lat * Math.PI) / 180) };
  const query = new URLSearchParams({
    assets: "data",
    algorithm: "slope",
    algorithm_params: JSON.stringify(params),
    dst_crs: "EPSG:3857",
  });
  return `${STATISTICS_URL}?${query}`;
}

function sampleArea(g: Polygon): Polygon {
  const [west, south, east, north] = bbox(g);
  const lat = (south + north) / 2;
  const widthM = (east - west) * M_PER_DEG * Math.cos((lat * Math.PI) / 180);
  const heightM = (north - south) * M_PER_DEG;
  if (Math.min(widthM, heightM) >= MIN_SAMPLE_M) return g;
  return squareAround([(west + east) / 2, lat], MIN_SAMPLE_M);
}

async function meanSlopes(url: string, tasks: AreaTask[], fetchFn: FetchFn): Promise<number[]> {
  const features = tasks.map((t) => ({
    type: "Feature",
    geometry: sampleArea(t.geometry),
    properties: {},
  }));
  const res = await fetchFn(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type: "FeatureCollection", features }),
  });
  if (!res.ok) throw new Error(`Could not load terrain data (HTTP ${res.status})`);
  const body = (await res.json()) as {
    features: { properties: { statistics: Record<string, { mean: number }> } }[];
  };
  return body.features.map((f) => Object.values(f.properties.statistics)[0]?.mean);
}

/** Add `slope_deg` to area tasks that don't have one yet. */
export async function withSlopes(
  tasks: Task[],
  progress: (message: string) => void = () => {},
  fetchFn: FetchFn = fetch,
): Promise<Task[]> {
  const todo = tasks.filter(isAreaTask).filter((t) => t.properties.slope_deg === undefined);
  if (!todo.length) return tasks;
  const [, south, , north] = bbox(todo.map((t) => t.geometry));
  const url = statisticsUrl((south + north) / 2);

  const chunks: AreaTask[][] = [];
  for (let i = 0; i < todo.length; i += TASKS_PER_REQUEST) {
    chunks.push(todo.slice(i, i + TASKS_PER_REQUEST));
  }
  const slopes = new Map<number, number>();
  for (let i = 0; i < chunks.length; i += PARALLEL_REQUESTS) {
    progress(`Scoring terrain (${i * TASKS_PER_REQUEST} of ${todo.length} tasks)`);
    const batch = chunks.slice(i, i + PARALLEL_REQUESTS);
    const means = (await Promise.all(batch.map((c) => meanSlopes(url, c, fetchFn)))).flat();
    batch.flat().forEach((t, j) => {
      // No mean when a task has no DEM pixels (e.g. over the sea).
      if (Number.isFinite(means[j])) slopes.set(t.properties.task_id, means[j]);
    });
  }

  return tasks.map((t) => {
    const slope = slopes.get(t.properties.task_id);
    if (slope === undefined) return t;
    return { ...t, properties: { ...t.properties, slope_deg: Math.round(slope * 10) / 10 } };
  });
}
