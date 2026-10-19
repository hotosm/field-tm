import { describe, expect, it, vi } from "vitest";
import { fetchRoads, OVERPASS_URL } from "../src/lib/io/overpass";

describe("fetchRoads", () => {
  it("queries the bbox and converts ways to tagged lines", async () => {
    const f = vi.fn(async (_url: string, _init?: RequestInit) =>
      Response.json({
        elements: [
          {
            type: "way",
            id: 1,
            tags: { highway: "primary" },
            geometry: [
              { lat: 1, lon: 2 },
              { lat: 3, lon: 4 },
            ],
          },
          { type: "way", id: 2, tags: { highway: "path" }, geometry: [{ lat: 1, lon: 2 }] },
        ],
      }),
    );
    const fc = await fetchRoads([10, 20, 11, 21], f);
    const [url, init] = f.mock.calls[0];
    expect(url).toBe(OVERPASS_URL);
    expect(String((init!.body as URLSearchParams).get("data"))).toContain(
      'way["highway"](20,10,21,11)',
    );
    expect(fc.features).toEqual([
      {
        type: "Feature",
        properties: { osm_id: 1, tags: { highway: "primary" } },
        geometry: {
          type: "LineString",
          coordinates: [
            [2, 1],
            [4, 3],
          ],
        },
      },
    ]);
  });

  it("reports HTTP errors", async () => {
    await expect(
      fetchRoads([0, 0, 1, 1], async () => new Response("", { status: 429 })),
    ).rejects.toThrow(/429/);
  });
});
