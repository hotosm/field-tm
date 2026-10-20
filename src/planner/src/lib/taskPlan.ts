import type { Feature, FeatureCollection, Polygon } from "geojson";

export const TASK_PLAN_VERSION = 1;
export const GROUP_RE = /^[A-Za-z0-9_-]+$/;
/** HTML pattern attribute equivalent (v-flag safe). */
export const GROUP_PATTERN = "[A-Za-z0-9_\\-]+";
const HEX_RE = /^#[0-9a-fA-F]{6}$/;

export type Algorithm =
  | "DIVIDE_BY_SQUARE"
  | "SPLIT_BY_ROADS"
  | "AVG_BUILDING_VORONOI"
  | "AVG_BUILDING_SKELETON"
  | "MANUAL";

export interface TaskProps {
  task_id: number;
  assigned_group?: string;
  assigned_to?: string;
  comment?: string;
  colour?: string;
  feature_count?: number;
}

export type Task = Feature<Polygon, TaskProps>;

export interface TaskPlan extends FeatureCollection<Polygon, TaskProps> {
  task_plan_version: 1;
  algorithm: Algorithm | string;
  params: Record<string, unknown>;
}

export class TaskPlanError extends Error {
  constructor(public errors: string[]) {
    super(errors.join("\n"));
  }
}

export function makePlan(
  tasks: Task[],
  algorithm: TaskPlan["algorithm"] = "MANUAL",
  params: Record<string, unknown> = {},
): TaskPlan {
  return { type: "FeatureCollection", task_plan_version: 1, algorithm, params, features: tasks };
}

/** Number tasks 1..n in their current order. */
export function renumber(tasks: Task[]): Task[] {
  return tasks.map((t, i) => ({ ...t, properties: { ...t.properties, task_id: i + 1 } }));
}

function isPosition(p: unknown): boolean {
  return (
    Array.isArray(p) && p.length >= 2 && p.every((n) => typeof n === "number" && Number.isFinite(n))
  );
}

function isPolygonCoords(c: unknown): boolean {
  return (
    Array.isArray(c) &&
    c.length > 0 &&
    c.every((ring) => Array.isArray(ring) && ring.length >= 4 && ring.every(isPosition))
  );
}

/** Return a list of problems; empty means valid. */
export function validate(input: unknown): string[] {
  const errors: string[] = [];
  const fc = input as Partial<TaskPlan> | null;
  if (
    !fc ||
    typeof fc !== "object" ||
    fc.type !== "FeatureCollection" ||
    !Array.isArray(fc.features)
  ) {
    return ["Not a GeoJSON FeatureCollection"];
  }
  if (fc.task_plan_version !== TASK_PLAN_VERSION) errors.push("task_plan_version must be 1");
  if (fc.features.length === 0) errors.push("Task plan has no tasks");
  const ids = new Set<number>();
  fc.features.forEach((f, i) => {
    const at = `Task ${i + 1}`;
    if (f?.geometry?.type !== "Polygon" || !isPolygonCoords(f.geometry.coordinates)) {
      errors.push(`${at}: geometry must be a Polygon`);
    }
    const p = (f?.properties ?? {}) as Partial<TaskProps>;
    if (!Number.isInteger(p.task_id) || (p.task_id as number) < 1) {
      errors.push(`${at}: task_id must be a positive integer`);
    } else if (ids.has(p.task_id as number)) {
      errors.push(`${at}: duplicate task_id ${p.task_id}`);
    } else {
      ids.add(p.task_id as number);
    }
    if (
      p.assigned_group != null &&
      (typeof p.assigned_group !== "string" || !GROUP_RE.test(p.assigned_group))
    ) {
      errors.push(`${at}: assigned_group may only contain letters, numbers, _ and -`);
    }
    for (const k of ["assigned_to", "comment"] as const) {
      if (p[k] != null && typeof p[k] !== "string") errors.push(`${at}: ${k} must be text`);
    }
    if (p.colour != null && (typeof p.colour !== "string" || !HEX_RE.test(p.colour))) {
      errors.push(`${at}: colour must be a hex colour like #d63f3f`);
    }
  });
  if (errors.length === 0 && ids.size > 0 && Math.max(...ids) !== ids.size) {
    errors.push("task_id values must be 1..n");
  }
  return errors;
}

/** Drop empty optional properties and unknown keys. */
function cleanProps(p: TaskProps): TaskProps {
  const out: TaskProps = { task_id: p.task_id };
  for (const k of ["assigned_group", "assigned_to", "comment", "colour"] as const) {
    const v = p[k]?.trim();
    if (v) out[k] = v;
  }
  if (typeof p.feature_count === "number") out.feature_count = p.feature_count;
  return out;
}

export function serialise(plan: TaskPlan): string {
  const out: TaskPlan = {
    ...plan,
    features: plan.features.map((f) => ({
      type: "Feature",
      geometry: f.geometry,
      properties: cleanProps(f.properties),
    })),
  };
  const errors = validate(out);
  if (errors.length) throw new TaskPlanError(errors);
  return JSON.stringify(out);
}

/** True for a task plan file, including older exports without `task_plan_version` (polygons with `task_id`). */
export function isTaskPlan(input: unknown): boolean {
  const fc = input as { type?: string; task_plan_version?: unknown; features?: Task[] };
  if (fc?.type !== "FeatureCollection" || !Array.isArray(fc.features) || !fc.features.length)
    return false;
  if (fc.task_plan_version != null) return true;
  return (
    fc.features.every(
      (f) => f?.geometry?.type === "Polygon" || f?.geometry?.type === "MultiPolygon",
    ) && fc.features.some((f) => Number.isInteger(f?.properties?.task_id))
  );
}

/** Parse and validate a task plan. Accepts single-part MultiPolygons and missing task_ids. */
export function parse(input: string | unknown): TaskPlan {
  const raw = (typeof input === "string" ? JSON.parse(input) : input) as TaskPlan;
  if (raw?.type === "FeatureCollection" && Array.isArray(raw.features)) {
    const needIds = raw.features.some((f) => !Number.isInteger(f?.properties?.task_id));
    raw.features = raw.features.map((f, i) => {
      const g = f?.geometry as unknown as { type: string; coordinates: unknown[] };
      const geometry =
        g?.type === "MultiPolygon" && g.coordinates.length === 1
          ? { type: "Polygon", coordinates: g.coordinates[0] }
          : g;
      const properties = { ...(f?.properties ?? {}) } as TaskProps;
      if (needIds) properties.task_id = i + 1;
      return { type: "Feature", geometry, properties } as Task;
    });
    raw.task_plan_version ??= 1;
    raw.algorithm ??= "MANUAL";
    raw.params ??= {};
  }
  const errors = validate(raw);
  if (errors.length) throw new TaskPlanError(errors);
  return raw;
}
