import { createDb } from "./db";
import { merge, split, splitByLine, type Db } from "./splitter";

const ops = { split, merge, splitByLine } as const;
export type Op = keyof typeof ops;

let db: Promise<Db> | null = null;

self.onmessage = async (e: MessageEvent<{ id: number; op: Op; args: unknown[] }>) => {
  const { id, op, args } = e.data;
  const progress = (msg: string) => self.postMessage({ id, progress: msg });
  try {
    if (!db) {
      progress("Loading the splitting engine (first time only)");
      db = createDb();
    }
    const fn = ops[op] as (db: Db, ...a: unknown[]) => Promise<unknown>;
    const result = await fn(await db, ...args, progress);
    self.postMessage({ id, result });
  } catch (err) {
    // A failed GEOS call can leave PGlite unusable, so start fresh next time.
    const failed = db;
    db = null;
    failed?.then((d) => d.close?.()).catch(() => {});
    self.postMessage({ id, error: err instanceof Error ? err.message : String(err) });
  }
};
