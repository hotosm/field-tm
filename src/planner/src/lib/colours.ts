import type { Task } from "./taskPlan";

// Colour-blind friendly palette (Okabe-Ito + Tol), HOT red first.
const PALETTE = [
  "#d63f3f",
  "#0072b2",
  "#e69f00",
  "#009e73",
  "#cc79a7",
  "#56b4e9",
  "#882255",
  "#117733",
  "#999933",
  "#6c4ba8",
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

/** Labels in use (team, else assignee) with their map colour, for the legend. */
export function legend(tasks: Task[]): { group: string; colour: string; count: number }[] {
  const m = new Map<string, { group: string; colour: string; count: number }>();
  for (const t of tasks) {
    const group = t.properties.assigned_group || t.properties.assigned_to || "";
    const e = m.get(group) ?? { group, colour: taskColour(t), count: 0 };
    e.count++;
    m.set(group, e);
  }
  return [...m.values()].sort((a, b) => a.group.localeCompare(b.group));
}
