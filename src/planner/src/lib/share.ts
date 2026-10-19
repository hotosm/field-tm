import type { Task } from "./taskPlan";
import { validate } from "./taskPlan";

const round = (n: number) => Math.round(n * 1e6) / 1e6;

function toBase64Url(s: string): string {
  const bytes = new TextEncoder().encode(s);
  let bin = "";
  bytes.forEach((b) => (bin += String.fromCharCode(b)));
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromBase64Url(s: string): string {
  const bin = atob(s.replace(/-/g, "+").replace(/_/g, "/"));
  return new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
}

/** Encode one task (geometry rounded to ~10 cm) for a #task= link. */
export function encodeTask(t: Task): string {
  const { building_count: _, ...props } = t.properties;
  const geometry = {
    type: "Polygon",
    coordinates: t.geometry.coordinates.map((r) => r.map(([x, y]) => [round(x), round(y)])),
  };
  return toBase64Url(JSON.stringify({ type: "Feature", geometry, properties: props }));
}

export function decodeTask(s: string): Task | null {
  try {
    const f = JSON.parse(fromBase64Url(s)) as Task;
    const ok = validate({
      type: "FeatureCollection",
      task_plan_version: 1,
      features: [{ ...f, properties: { ...f.properties, task_id: 1 } }],
    });
    return ok.length ? null : f;
  } catch {
    return null;
  }
}

export function shareUrl(t: Task, base: string): string {
  const u = new URL(base);
  u.search = "";
  u.hash = `task=${encodeTask(t)}`;
  return u.toString();
}
