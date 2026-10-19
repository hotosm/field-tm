import { defineConfig } from "vitest/config";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { fileURLToPath } from "node:url";

const algorithms = fileURLToPath(
  new URL("../backend/packages/area-splitter/area_splitter/algorithms", import.meta.url),
);

export default defineConfig({
  // './' keeps asset paths relative, so the same build works at / , a sub-path, or /planner/.
  base: process.env.PLANNER_BASE ?? "./",
  plugins: [svelte()],
  resolve: { alias: { "@algorithms": algorithms } },
  server: { fs: { allow: [".", algorithms] } },
  optimizeDeps: { exclude: ["@electric-sql/pglite", "@electric-sql/pglite-postgis"] },
  worker: { format: "es", rolldownOptions: { checks: { eval: false } } },
  build: {
    outDir: "dist",
    target: "es2022",
    chunkSizeWarningLimit: 2000,
    // PGlite's Emscripten glue uses eval; nothing we can change.
    rolldownOptions: { checks: { eval: false } },
  },
  test: { include: ["tests/**/*.test.ts"], testTimeout: 120_000, hookTimeout: 120_000 },
});
