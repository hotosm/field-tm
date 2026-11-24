import type { Geometry } from "geojson";
import type { ExpressionSpecification, Map } from "maplibre-gl";
import { legend } from "./colours";
import { bbox } from "./geo";
import type { Task } from "./taskPlan";

const esc = (s: string) =>
  s.replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!,
  );

const STYLE = `<style>
  body { font-family: system-ui, sans-serif; margin: 1.5cm; color: #111; }
  h1 { font-size: 1.4rem; margin: 0 0 0.5rem; }
  dl { display: grid; grid-template-columns: auto 1fr; gap: 0.2rem 1rem; margin: 0 0 1rem; }
  dt { font-weight: 600; }
  dd { margin: 0; }
  table { border-collapse: collapse; margin: 0 0 1rem; }
  th, td { border: 1px solid #999; padding: 0.2rem 0.5rem; text-align: left; vertical-align: top; }
  .swatch { display: inline-block; width: 0.8rem; height: 0.8rem; margin-right: 0.3rem; }
  h2 { font-size: 1.2rem; margin: 0 0 0.5rem; }
  .team { break-before: page; }
  img { width: 100%; border: 1px solid #999; }
  footer { font-size: 0.75rem; color: #555; margin-top: 0.5rem; }
</style>`;

const page = (heading: string, body: string) =>
  `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${esc(heading)}</title>${STYLE}</head><body>
<h1>${esc(heading)}</h1>
${body}
<footer>Map data © OpenStreetMap contributors, OpenFreeMap. Printed from the Field-TM Task Planner on ${new Date().toLocaleDateString()}.</footer>
</body></html>`;

const withTitle = (heading: string, title?: string) => (title ? `${heading} - ${title}` : heading);

/** HTML for a printable task sheet. */
export function taskSheet(task: Task, mapImage: string, title?: string): string {
  const p = task.properties;
  const rows = [
    ["Team", p.assigned_group],
    ["Features to map", p.feature_count?.toString()],
    ["Comment", p.comment],
  ].filter(([, v]) => v);
  return page(
    withTitle(`Task ${p.task_id}`, title),
    `<dl>${rows.map(([k, v]) => `<dt>${esc(k!)}</dt><dd>${esc(v!)}</dd>`).join("")}</dl>
<img src="${mapImage}" alt="Map of task ${p.task_id}">`,
  );
}

const teamName = (group: string) => esc(group || "Unassigned");

/** HTML for an overview of who maps where, then a page per team with its tasks highlighted. */
export function teamsSheet(
  tasks: Task[],
  overview: string,
  teamMaps: Record<string, string>,
  title?: string,
): string {
  const teams = legend(tasks).map((item) => ({
    ...item,
    ids: tasks
      .filter((t) => (t.properties.assigned_group ?? "") === item.group)
      .map((t) => t.properties.task_id)
      .join(", "),
  }));
  const rows = teams.map(({ group, colour, count, hilly, ids }) => {
    const name = `<span class="swatch" style="background:${colour}"></span>${teamName(group)}`;
    return `<tr><td>${name}</td><td>${count}</td><td>${hilly}</td><td>${ids}</td></tr>`;
  });
  const pages = teams
    .filter(({ group }) => teamMaps[group])
    .map(
      ({ group, colour, count, hilly, ids }) => `<section class="team">
<h2><span class="swatch" style="background:${colour}"></span>Team ${teamName(group)}</h2>
<dl><dt>Tasks</dt><dd>${count}</dd><dt>Hilly</dt><dd>${hilly}</dd><dt>Task numbers</dt><dd>${ids}</dd></dl>
<img src="${teamMaps[group]}" alt="Map of team ${teamName(group)}'s tasks">
</section>`,
    );
  return page(
    withTitle("Teams", title),
    `<table><thead><tr><th>Team</th><th>Tasks</th><th>Hilly</th><th>Task numbers</th></tr></thead>
<tbody>${rows.join("")}</tbody></table>
<img src="${overview}" alt="Map of tasks by team">
${pages.join("\n")}`,
  );
}

type PaintProperty = Parameters<Map["setPaintProperty"]>[1];

/** Fade other teams' tasks so `team` stands out. Returns a function that restores the map. */
function highlightTeam(map: Map, team: string): () => void {
  const mine: ExpressionSpecification = ["==", ["get", "assigned_group"], team];
  // Layer ids from MapView.svelte.
  const changes: [string, PaintProperty, ExpressionSpecification][] = [
    ["tasks-fill", "fill-opacity", ["case", mine, 0.5, 0]],
    ["tasks-line", "line-color", ["case", mine, ["get", "_colour"], "#999"]],
    ["tasks-line", "line-width", ["case", mine, 3, 1]],
    ["tasks-label", "text-opacity", ["case", mine, 1, 0.4]],
  ];
  const before = changes.map(([layer, prop]) => map.getPaintProperty(layer, prop));
  changes.forEach(([layer, prop, value]) => map.setPaintProperty(layer, prop, value));
  return () => changes.forEach(([layer, prop], i) => map.setPaintProperty(layer, prop, before[i]));
}

/** Zoom the map to `geometries` and return it as a PNG data URL. */
async function capture(map: Map, geometries: Geometry[]): Promise<string> {
  const [w, s, e, n] = bbox(geometries);
  map.fitBounds(
    [
      [w, s],
      [e, n],
    ],
    { padding: 40, animate: false },
  );
  await new Promise((r) => map.once("idle", r));
  // Read the canvas inside a render event, before WebGL clears the buffer.
  return new Promise<string>((resolve) => {
    map.once("render", () => resolve(map.getCanvas().toDataURL("image/png")));
    map.triggerRepaint();
  });
}

/** Build the sheet from map captures and open the browser's print dialog (Save as PDF). */
async function printSheet(sheet: () => Promise<string>): Promise<void> {
  // Open the window during the click so pop-up blockers allow it.
  const win = window.open("", "_blank");
  if (!win) throw new Error("Allow pop-ups for this site to print.");
  win.document.write("<p style='font-family:sans-serif'>Preparing the map…</p>");
  const html = await sheet();
  win.document.open();
  win.document.write(html);
  win.document.close();
  const loading = [...win.document.images]
    .filter((img) => !img.complete)
    .map((img) => new Promise((r) => (img.onload = r)));
  await Promise.all(loading);
  win.focus();
  win.print();
}

export function printTask(map: Map, task: Task, title?: string): Promise<void> {
  return printSheet(async () => taskSheet(task, await capture(map, [task.geometry]), title));
}

export function printTeams(map: Map, tasks: Task[], title?: string): Promise<void> {
  return printSheet(async () => {
    const overview = await capture(
      map,
      tasks.map((t) => t.geometry),
    );
    const teamMaps: Record<string, string> = {};
    for (const { group } of legend(tasks).filter((item) => item.group)) {
      const mine = tasks.filter((t) => t.properties.assigned_group === group);
      const restore = highlightTeam(map, group);
      try {
        teamMaps[group] = await capture(
          map,
          mine.map((t) => t.geometry),
        );
      } finally {
        restore();
      }
    }
    return teamsSheet(tasks, overview, teamMaps, title);
  });
}
