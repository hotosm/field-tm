import { describe, expect, it } from "vitest";
import type { StyleSpecification } from "maplibre-gl";
import { BASEMAP_URL, cleanStyle, loadBasemap } from "../src/lib/basemap";

const style = {
  version: 8,
  sources: {},
  layers: [
    { id: "road", type: "line", source: "x" },
    { id: "highway-shield-non-us", type: "symbol", source: "x" },
  ],
} as unknown as StyleSpecification;

describe("basemap", () => {
  it("drops road shield layers", () => {
    expect(cleanStyle(style).layers.map((l) => l.id)).toEqual(["road"]);
  });

  it("falls back to the style URL when the fetch fails", async () => {
    const failing = (() => Promise.reject(new Error("offline"))) as unknown as typeof fetch;
    expect(await loadBasemap(failing)).toBe(BASEMAP_URL);
  });

  it("returns the cleaned style", async () => {
    const ok = (() =>
      Promise.resolve(new Response(JSON.stringify(style)))) as unknown as typeof fetch;
    const out = (await loadBasemap(ok)) as StyleSpecification;
    expect(out.layers).toHaveLength(1);
  });
});
