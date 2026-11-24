import type { Task } from "./taskPlan";
import { decodeTask } from "./share";

export type Mode =
  | { kind: "standalone"; aoi?: string; features?: string; roads?: string; returnTo?: string }
  | { kind: "fieldtm"; project: string; view: boolean }
  | { kind: "task"; task: Task };

/** Lets relative URLs (fetched from this site) pass the http(s) check. */
const RELATIVE_BASE = "https://x";

/** `v` if it is an http(s) URL. Relative URLs are accepted only with a `base`. */
function httpUrl(v: string | null, base?: string): string | undefined {
  if (!v) return undefined;
  try {
    return ["http:", "https:"].includes(new URL(v, base).protocol) ? v : undefined;
  } catch {
    return undefined;
  }
}

export function parseMode(search: string, hash = ""): Mode {
  const q = new URLSearchParams(search);
  const h = new URLSearchParams(hash.replace(/^#/, ""));
  const shared = h.get("task") ?? q.get("task");
  if (shared) {
    const task = decodeTask(shared);
    if (task) return { kind: "task", task };
  }
  const project = q.get("fieldtm");
  if (project && /^\d+$/.test(project)) {
    return { kind: "fieldtm", project, view: ["1", "true"].includes(q.get("view") ?? "") };
  }
  const url = (k: string) => httpUrl(q.get(k), RELATIVE_BASE);
  return {
    kind: "standalone",
    aoi: url("aoi"),
    features: url("features"),
    roads: url("roads"),
    returnTo: httpUrl(q.get("return_to")),
  };
}
