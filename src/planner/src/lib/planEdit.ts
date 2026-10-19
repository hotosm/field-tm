import type { Polygon } from "geojson";
import type { Task, TaskProps } from "./taskPlan";
import { renumber } from "./taskPlan";

export type Assignment = Pick<TaskProps, "assigned_group" | "assigned_to" | "comment" | "colour">;

/** Replace tasks `ids` with `geoms`, placed where the first replaced task was. Keeps the first task's assignment. */
export function replaceTasks(
  tasks: Task[],
  ids: number[],
  geoms: Polygon[],
  buildingCounts?: number[],
): Task[] {
  const idx = tasks.findIndex((t) => ids.includes(t.properties.task_id));
  if (idx < 0) return tasks;
  const { building_count: _, ...inherit } = tasks[idx].properties;
  const added: Task[] = geoms.map((geometry, i) => ({
    type: "Feature",
    geometry,
    properties: { ...inherit, ...(buildingCounts ? { building_count: buildingCounts[i] } : {}) },
  }));
  const kept = tasks.filter((t) => !ids.includes(t.properties.task_id));
  const before = tasks.slice(0, idx).filter((t) => !ids.includes(t.properties.task_id)).length;
  return renumber([...kept.slice(0, before), ...added, ...kept.slice(before)]);
}

export function removeTasks(tasks: Task[], ids: number[]): Task[] {
  return renumber(tasks.filter((t) => !ids.includes(t.properties.task_id)));
}

/** Apply an assignment to tasks; empty strings clear a field, undefined leaves it alone. */
export function assign(tasks: Task[], ids: number[], patch: Assignment): Task[] {
  return tasks.map((t) => {
    if (!ids.includes(t.properties.task_id)) return t;
    const properties = { ...t.properties };
    for (const [k, v] of Object.entries(patch) as [keyof Assignment, string | undefined][]) {
      if (v === undefined) continue;
      if (v.trim()) properties[k] = v.trim();
      else delete properties[k];
    }
    return { ...t, properties };
  });
}

export function sumBuildings(tasks: Task[], ids: number[]): number | undefined {
  const sel = tasks.filter((t) => ids.includes(t.properties.task_id));
  return sel.every((t) => typeof t.properties.building_count === "number")
    ? sel.reduce((s, t) => s + (t.properties.building_count ?? 0), 0)
    : undefined;
}
