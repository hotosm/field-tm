import { PGlite, type Extension } from "@electric-sql/pglite";
import type { Db } from "./splitter";

/**
 * @electric-sql/pglite-postgis's extension, pointed at a trimmed bundle from
 * scripts/slim-postgis.sh. It cuts the one-off engine download by ~12 MB, which
 * matters on slow field connections. Keep `setup` in step on PGlite upgrades.
 */
const postgis: Extension = {
  name: "postgis",
  setup: async (_pg, emscriptenOpts) => {
    emscriptenOpts.PGLITE_ENV.PROJ_DATA = "/pglite/share/proj";
    return { emscriptenOpts, bundlePath: new URL("./postgis-slim.tar.gz", import.meta.url) };
  },
};

export async function createDb(): Promise<Db> {
  const pg = await PGlite.create({ extensions: { postgis } });
  await pg.exec("CREATE EXTENSION IF NOT EXISTS postgis;");
  return pg as unknown as Db;
}
