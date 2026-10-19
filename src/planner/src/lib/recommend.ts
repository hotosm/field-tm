import { areaM2, type Area } from "./geo";
import type { SplitAlgorithm, SplitParams } from "./engine/splitter";

export const MAX_TASKS = 100;
export const BUILDINGS_PER_TASK = 100;

/** Sensible defaults: aim for <= ~100 tasks and <= ~100 buildings per task. */
export function recommend(
  aoi: Area,
  buildings: number,
): { algorithm: SplitAlgorithm; params: SplitParams; note: string } {
  if (buildings > 0) {
    const perTask = Math.min(
      BUILDINGS_PER_TASK,
      Math.max(10, Math.ceil(buildings / MAX_TASKS / 10) * 10),
    );
    return {
      algorithm: "AVG_BUILDING_VORONOI",
      params: { num_buildings: perTask },
      note: `${buildings} buildings: about ${perTask} per task gives ~${Math.ceil(buildings / perTask)} tasks.`,
    };
  }
  return {
    algorithm: "DIVIDE_BY_SQUARE",
    params: { cell_size: gridSize(aoi) },
    note: "No data: a square grid needs nothing else.",
  };
}

/** Cell size (m, rounded to a nice step) giving roughly <= MAX_TASKS cells. */
export function gridSize(aoi: Area): number {
  const raw = Math.sqrt(areaM2(aoi) / MAX_TASKS);
  const step = raw < 200 ? 10 : raw < 1000 ? 50 : 100;
  return Math.max(50, Math.ceil(raw / step) * step);
}

export function estimateTasks(
  aoi: Area,
  algorithm: SplitAlgorithm,
  params: SplitParams,
  buildings: number,
): number | null {
  if (algorithm === "DIVIDE_BY_SQUARE" && params.cell_size)
    return Math.ceil(areaM2(aoi) / params.cell_size ** 2);
  if (algorithm === "AVG_BUILDING_VORONOI" && params.num_buildings)
    return Math.ceil(buildings / params.num_buildings);
  return null;
}
