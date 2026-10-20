import type { LineString, Polygon } from "geojson";
import type { Task } from "../taskPlan";
import type { SplitInput } from "./splitter";
import type { Op } from "./worker";

type Pending = {
  resolve: (v: any) => void;
  reject: (e: Error) => void;
  onProgress?: (m: string) => void;
};

/** GEOS/CGAL can hang on rare inputs; stop the worker rather than spin forever. */
const TIMEOUT_MS = 10 * 60_000;

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
    const timer = setTimeout(() => {
      worker?.terminate();
      worker = null;
      const err = new Error(
        "This took too long and was stopped. Try larger tasks or another method.",
      );
      for (const p of pending.values()) p.reject(err);
      pending.clear();
    }, TIMEOUT_MS);
    const done =
      <A>(f: (a: A) => void) =>
      (a: A) => {
        clearTimeout(timer);
        f(a);
      };
    pending.set(id, { resolve: done(resolve), reject: done(reject), onProgress });
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
