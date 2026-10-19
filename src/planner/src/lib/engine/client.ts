import type { LineString, Polygon } from "geojson";
import type { Task } from "../taskPlan";
import type { SplitInput } from "./splitter";
import type { Op } from "./worker";

type Pending = {
  resolve: (v: any) => void;
  reject: (e: Error) => void;
  onProgress?: (m: string) => void;
};

let worker: Worker | null = null;
let nextId = 0;
const pending = new Map<number, Pending>();

function call<T>(op: Op, args: unknown[], onProgress?: (m: string) => void): Promise<T> {
  if (!worker) {
    // Lazy: PGlite + PostGIS (~35 MB) only load when the user first splits or edits.
    worker = new Worker(new URL("./worker.ts", import.meta.url), { type: "module" });
    worker.onmessage = (e) => {
      const { id, progress, result, error } = e.data;
      const p = pending.get(id);
      if (!p) return;
      if (progress) return p.onProgress?.(progress);
      pending.delete(id);
      if (error) p.reject(new Error(error));
      else p.resolve(result);
    };
  }
  const id = nextId++;
  return new Promise<T>((resolve, reject) => {
    pending.set(id, { resolve, reject, onProgress });
    // $state proxies can't be cloned; plain JSON round-trip strips them.
    worker!.postMessage({ id, op, args: JSON.parse(JSON.stringify(args)) });
  });
}

export const engine = {
  split: (input: SplitInput, onProgress?: (m: string) => void) =>
    call<Task[]>("split", [input], onProgress),
  merge: (polygons: Polygon[]) => call<Polygon>("merge", [polygons]),
  splitByLine: (polygon: Polygon, line: LineString) =>
    call<Polygon[]>("splitByLine", [polygon, line]),
};
