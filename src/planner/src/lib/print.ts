import type { Map } from "maplibre-gl";
import { bbox } from "./geo";
import type { Task } from "./taskPlan";

const esc = (s: string) =>
  s.replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!,
  );

/** HTML for a printable task sheet. */
export function taskSheet(task: Task, mapImage: string, title?: string): string {
  const p = task.properties;
  const rows = [
    ["Team", p.assigned_group],
    ["Assigned to", p.assigned_to],
    ["Features to map", p.feature_count?.toString()],
    ["Comment", p.comment],
  ].filter(([, v]) => v);
  const heading = `Task ${p.task_id}${title ? ` - ${title}` : ""}`;
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${esc(heading)}</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 1.5cm; color: #111; }
  h1 { font-size: 1.4rem; margin: 0 0 0.5rem; }
  dl { display: grid; grid-template-columns: auto 1fr; gap: 0.2rem 1rem; margin: 0 0 1rem; }
  dt { font-weight: 600; }
  dd { margin: 0; }
  img { width: 100%; border: 1px solid #999; }
  footer { font-size: 0.75rem; color: #555; margin-top: 0.5rem; }
</style></head><body>
<h1>${esc(heading)}</h1>
<dl>${rows.map(([k, v]) => `<dt>${esc(k!)}</dt><dd>${esc(v!)}</dd>`).join("")}</dl>
<img src="${mapImage}" alt="Map of task ${p.task_id}">
<footer>Map data © OpenStreetMap contributors, OpenFreeMap. Printed from the Field-TM Task Planner on ${new Date().toLocaleDateString()}.</footer>
</body></html>`;
}

/** Zoom to the task, capture the map and open the browser's print dialog (Save as PDF). */
export async function printTask(map: Map, task: Task, title?: string): Promise<void> {
  // Open the window during the click so pop-up blockers allow it.
  const win = window.open("", "_blank");
  if (!win) throw new Error("Allow pop-ups for this site to print the task.");
  win.document.write("<p style='font-family:sans-serif'>Preparing the task map…</p>");
  const [w, s, e, n] = bbox(task.geometry);
  map.fitBounds(
    [
      [w, s],
      [e, n],
    ],
    { padding: 40, animate: false },
  );
  await new Promise((r) => map.once("idle", r));
  // Read the canvas inside a render event, before WebGL clears the buffer.
  const image = await new Promise<string>((resolve) => {
    map.once("render", () => resolve(map.getCanvas().toDataURL("image/png")));
    map.triggerRepaint();
  });
  win.document.open();
  win.document.write(taskSheet(task, image, title));
  win.document.close();
  const img = win.document.querySelector("img");
  const go = () => {
    win.focus();
    win.print();
  };
  if (img && !img.complete) img.onload = go;
  else go();
}
