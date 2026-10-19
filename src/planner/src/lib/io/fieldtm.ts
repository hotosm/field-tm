import type { FetchFn } from "./files";
import type { FeatureCollection, Geometry, Feature } from "geojson";
import type { TaskPlan } from "../taskPlan";
import { serialise } from "../taskPlan";

export interface PlannerInput {
  project: { id: number; name: string; field_mapping_app: string };
  aoi: Geometry | Feature | FeatureCollection;
  features: FeatureCollection | null;
  task_plan: FeatureCollection | null;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
  get isAuth() {
    return this.status === 401 || this.status === 403;
  }
}

export const loginUrl = (returnTo: string) => `/login?return_to=${encodeURIComponent(returnTo)}`;
export const projectUrl = (id: string | number) => `/projects/${encodeURIComponent(String(id))}`;
const api = (id: string | number, path: string) =>
  `/api/v1/projects/${encodeURIComponent(String(id))}/${path}`;

async function check(res: Response) {
  if (res.ok) return res.json();
  let detail = "";
  try {
    const body = await res.json();
    detail = body.detail ?? body.message ?? "";
  } catch {
    /* non-JSON error body */
  }
  const messages: Record<number, string> = {
    401: "Please log in to Field-TM to continue.",
    403: "You need to be a project manager of this project.",
    404: "Project not found.",
  };
  throw new ApiError(
    res.status,
    messages[res.status] ?? (detail || `Field-TM error (HTTP ${res.status})`),
  );
}

export async function getPlannerInput(
  id: string | number,
  fetchFn: FetchFn = fetch,
): Promise<PlannerInput> {
  return check(await fetchFn(api(id, "planner-input"), { credentials: "same-origin" }));
}

export async function saveTaskPlan(
  id: string | number,
  plan: TaskPlan,
  fetchFn: FetchFn = fetch,
): Promise<{ task_count: number }> {
  return check(
    await fetchFn(api(id, "task-plan"), {
      method: "PUT",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: serialise(plan),
    }),
  );
}
