import type { Area } from "./geo";
import type { Task, TaskPlan } from "./taskPlan";
import { serialise } from "./taskPlan";

const esc = (s: string) =>
  s.replace(
    /[<>&'"]/g,
    (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", "'": "&apos;", '"': "&quot;" })[c]!,
  );

export function taskName(t: Task): string {
  const team = t.properties.assigned_group;
  return `Task ${t.properties.task_id}${team ? ` (${team})` : ""}`;
}

export function taskGeoJSON(t: Task): string {
  return JSON.stringify({ type: "FeatureCollection", features: [t] }, null, 2);
}

const gpxSegments = (rings: number[][][]) =>
  rings
    .map(
      (ring) =>
        `      <trkseg>\n${ring.map(([lon, lat]) => `        <trkpt lat="${lat}" lon="${lon}"/>`).join("\n")}\n      </trkseg>`,
    )
    .join("\n");

/** A GPX document with one track whose segments are the given rings. */
function gpxTrack(name: string, rings: number[][][], desc = ""): string {
  const title = esc(name);
  const description = desc ? `\n    <desc>${esc(desc)}</desc>` : "";
  return `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Field-TM Task Planner" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata><name>${title}</name></metadata>
  <trk>
    <name>${title}</name>${description}
${gpxSegments(rings)}
  </trk>
</gpx>
`;
}

/** GPX with an area task as a closed track, or a route as tracks; widely supported by mapping apps. */
export function taskGPX(t: Task): string {
  return gpxTrack(taskName(t), t.geometry.coordinates, t.properties.comment);
}

export function planGeoJSON(plan: TaskPlan): string {
  return serialise(plan);
}

/** The drawn area on its own, as a single-feature GeoJSON for QGIS, JOSM or other tools. */
export function aoiGeoJSON(aoi: Area): string {
  return JSON.stringify(
    {
      type: "FeatureCollection",
      features: [{ type: "Feature", geometry: aoi, properties: { name: "Area of interest" } }],
    },
    null,
    2,
  );
}

/** GPX with each ring of the area (outer and holes) as a closed track segment. */
export function aoiGPX(aoi: Area): string {
  return gpxTrack(
    "Area of interest",
    aoi.type === "Polygon" ? aoi.coordinates : aoi.coordinates.flat(),
  );
}
