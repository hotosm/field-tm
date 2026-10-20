import { describe, expect, it, vi } from "vitest";
import { fetchRoads, POSTPASS_URL } from "../src/lib/io/postpass";

describe("fetchRoads", () => {
  it("queries the bbox and returns the features", async () => {
    const feature = {
      type: "Feature",
      properties: { osm_id: 1, tags: { highway: "primary" } },
      geometry: {
        type: "MultiLineString",
        coordinates: [
          [
            [2, 1],
            [4, 3],
          ],
        ],
      },
    };
    const f = vi.fn(async (_url: string, _init?: RequestInit) =>
      Response.json({ type: "FeatureCollection", features: [feature] }),
    );
    const fc = await fetchRoads([10, 20, 11, 21], f);
    const [url, init] = f.mock.calls[0];
    expect(url).toBe(POSTPASS_URL);
    const sql = String((init!.body as URLSearchParams).get("data"));
    expect(sql).toContain("FROM postpass_line");
    expect(sql).toContain("ST_MakeEnvelope(10, 20, 11, 21, 4326)");
    expect(fc).toEqual({ type: "FeatureCollection", features: [feature] });
  });

  it("reports HTTP errors", async () => {
    await expect(
      fetchRoads([0, 0, 1, 1], async () => new Response("", { status: 429 })),
    ).rejects.toThrow(/429/);
  });
});
