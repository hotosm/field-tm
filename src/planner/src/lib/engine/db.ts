import { PGlite } from "@electric-sql/pglite";
import { postgis } from "@electric-sql/pglite-postgis";
import type { Db } from "./splitter";

export async function createDb(): Promise<Db> {
  const pg = await PGlite.create({ extensions: { postgis } });
  await pg.exec("CREATE EXTENSION IF NOT EXISTS postgis;");
  return pg as unknown as Db;
}
