import type { Task } from "./taskPlan";
import { decodeTask } from "./share";

export type Mode =
  | { kind: "standalone"; aoi?: string; features?: string; roads?: string; returnTo?: string }
  | { kind: "fieldtm"; project: string; view: boolean }
  | { kind: "task"; task: Task };

/** An absolute http(s) URL to send the user back to, e.g. a Field-TM project page. */
function returnUrl(v: string | null): string | undefined {
  try {
    return v && ["http:", "https:"].includes(new URL(v).protocol)
      ? new URL(v).toString()
      : undefined;
  } catch {
    return undefined;
  }
}

const isHttpUrl = (s: string) => {
  try {
    return ["http:", "https:"].includes(new URL(s, "https://x").protocol);
  } catch {
    return false;
  }
};

export function parseMode(search: string, hash = ""): Mode {
  const q = new URLSearchParams(search);
  const h = new URLSearchParams(hash.replace(/^#/, ""));
  const shared = h.get("task") ?? q.get("task");
  if (shared) {
    const task = decodeTask(shared);
    if (task) return { kind: "task", task };
  }
  const project = q.get("project");
  if (project && /^\d+$/.test(project)) {
    return { kind: "fieldtm", project, view: ["1", "true"].includes(q.get("view") ?? "") };
  }
  const url = (k: string) => {
    const v = q.get(k);
    return v && isHttpUrl(v) ? v : undefined;
  };
  return {
    kind: "standalone",
    aoi: url("aoi"),
    features: url("features"),
    roads: url("roads"),
    returnTo: returnUrl(q.get("return_to")),
  };
}
