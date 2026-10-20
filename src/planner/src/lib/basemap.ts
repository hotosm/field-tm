import type { Map, StyleSpecification } from "maplibre-gl";

export const BASEMAP_URL = "https://tiles.openfreemap.org/styles/liberty";

/** Drop the road shield layers: their filters are invalid in current MapLibre and we don't need them. */
export function cleanStyle(style: StyleSpecification): StyleSpecification {
  return { ...style, layers: style.layers.filter((l) => !l.id.includes("shield")) };
}

/** The cleaned basemap style, or its URL if it can't be fetched. */
export async function loadBasemap(
  fetchFn: typeof fetch = fetch,
): Promise<StyleSpecification | string> {
  try {
    const res = await fetchFn(BASEMAP_URL);
    if (!res.ok) return BASEMAP_URL;
    return cleanStyle((await res.json()) as StyleSpecification);
  } catch {
    return BASEMAP_URL;
  }
}

/** The style references some POI icons its sprite lacks; use a blank image instead of warning. */
export function addBlankImage(map: Map, id: string) {
  if (!map.hasImage(id)) map.addImage(id, { width: 1, height: 1, data: new Uint8Array(4) });
}
