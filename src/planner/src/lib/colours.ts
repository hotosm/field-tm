import { isAreaTask, type Task } from "./taskPlan";

// Sasha Trubetskoy's distinct colours: easier to tell apart on the map than a colour-blind safe set.
export const PALETTE = [
  "#e6194b",
  "#4363d8",
  "#f58231",
  "#3cb44b",
  "#911eb4",
  "#ffe119",
  "#42d4f4",
  "#f032e6",
  "#9a6324",
  "#000075",
];
export const UNASSIGNED = "#7f7f7f";

export function groupColour(group?: string): string {
  if (!group) return UNASSIGNED;
  let h = 0;
  for (const c of group) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return PALETTE[h % PALETTE.length];
}

export function taskColour(t: Task): string {
  return t.properties.colour || groupColour(t.properties.assigned_group);
}

/** Unassigned routes cycle through the palette so neighbouring routes stand apart. */
export function mapColour(t: Task): string {
  const colour = taskColour(t);
  if (isAreaTask(t) || colour !== UNASSIGNED) return colour;
  return PALETTE[t.properties.task_id % PALETTE.length];
}

export interface LegendItem {
  group: string;
  colour: string;
  count: number;
  hilly: number;
}

/** Teams in use with their map colour, for the legend. */
export function legend(tasks: Task[]): LegendItem[] {
  const m = new Map<string, LegendItem>();
  for (const t of tasks) {
    const group = t.properties.assigned_group ?? "";
    const e = m.get(group) ?? { group, colour: taskColour(t), count: 0, hilly: 0 };
    e.count++;
    if (t.properties.hilly) e.hilly++;
    m.set(group, e);
  }
  return [...m.values()].sort((a, b) => a.group.localeCompare(b.group));
}
