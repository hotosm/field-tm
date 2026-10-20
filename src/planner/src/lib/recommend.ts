import { areaM2, type Area } from "./geo";
import {
  SKELETON_MAX_FEATURES,
  SKELETON_MAX_TASKS,
  type SplitAlgorithm,
  type SplitParams,
} from "./engine/splitter";

export const MAX_TASKS = 100;
export const FEATURES_PER_TASK = 100;

/**
 * Sensible defaults: aim for <= ~100 tasks and <= ~100 features per task.
 * Prefer the street-following split (straight skeleton) when it is fast enough.
 */
export function recommend(
  aoi: Area,
  features: number,
  lines = 0,
): { algorithm: SplitAlgorithm; params: SplitParams; note: string } {
  if (features > 0) {
    const perTask = Math.min(
      FEATURES_PER_TASK,
      Math.max(10, Math.ceil(features / MAX_TASKS / 10) * 10),
    );
    const tasks = Math.ceil(features / perTask);
    const skeleton = features <= SKELETON_MAX_FEATURES && tasks <= SKELETON_MAX_TASKS;
    return {
      algorithm: skeleton ? "AVG_BUILDING_SKELETON" : "AVG_BUILDING_VORONOI",
      params: { num_buildings: perTask },
      note: skeleton
        ? `${features} features: about ${perTask} per task gives ~${tasks} tasks, with edges along streets.`
        : `${features} features: about ${perTask} per task gives ~${tasks} tasks. The quick method suits this much data.`,
    };
  }
  if (lines > 0) {
    return {
      algorithm: "SPLIT_BY_ROADS",
      params: {},
      note: "Roads loaded: split into blocks between main roads, rivers and railways.",
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
  features: number,
): number | null {
  if (algorithm === "DIVIDE_BY_SQUARE" && params.cell_size)
    return Math.ceil(areaM2(aoi) / params.cell_size ** 2);
  if (
    (algorithm === "AVG_BUILDING_VORONOI" || algorithm === "AVG_BUILDING_SKELETON") &&
    params.num_buildings
  )
    return Math.ceil(features / params.num_buildings);
  return null;
}
