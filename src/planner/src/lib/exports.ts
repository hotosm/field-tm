import type { Task, TaskPlan } from "./taskPlan";
import { serialise } from "./taskPlan";

const esc = (s: string) =>
  s.replace(
    /[<>&'"]/g,
    (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", "'": "&apos;", '"': "&quot;" })[c]!,
  );

export function taskName(t: Task): string {
  const who = t.properties.assigned_to || t.properties.assigned_group;
  return `Task ${t.properties.task_id}${who ? ` (${who})` : ""}`;
}

export function taskGeoJSON(t: Task): string {
  return JSON.stringify({ type: "FeatureCollection", features: [t] }, null, 2);
}

/** GPX with the task boundary as a closed track; widely supported by mapping apps. */
export function taskGPX(t: Task): string {
  const name = esc(taskName(t));
  const desc = t.properties.comment ? `\n    <desc>${esc(t.properties.comment)}</desc>` : "";
  const segs = t.geometry.coordinates
    .map(
      (ring) =>
        `      <trkseg>\n${ring.map(([lon, lat]) => `        <trkpt lat="${lat}" lon="${lon}"/>`).join("\n")}\n      </trkseg>`,
    )
    .join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Field-TM Task Planner" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata><name>${name}</name></metadata>
  <trk>
    <name>${name}</name>${desc}
${segs}
  </trk>
</gpx>
`;
}

export function planGeoJSON(plan: TaskPlan): string {
  return serialise(plan);
}
