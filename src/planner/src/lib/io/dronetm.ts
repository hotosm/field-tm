import { toArea, type Area } from "../geo";
import { makePlan, parse, type Task, type TaskPlan } from "../taskPlan";
import { fetchJson, type FetchFn } from "./files";

/** The fields we use from Drone-TM's public `GET /projects/{id}`. */
interface DroneTmProject {
  name: string;
  outline: unknown;
  no_fly_zones: unknown;
  tasks: { project_task_index: number; outline: unknown }[];
}

export interface DroneTmInput {
  name: string;
  aoi: Area;
  noFlyZones: Area | null;
  /** Task ids match Drone-TM's task numbers. */
  plan: TaskPlan;
}

export async function getDroneTmProject(
  url: string,
  fetchFn: FetchFn = fetch,
): Promise<DroneTmInput> {
  const project = (await fetchJson(url, undefined, fetchFn)) as DroneTmProject;
  if (!Array.isArray(project?.tasks)) throw new Error("This link is not a Drone-TM project.");
  const tasks: Task[] = [...project.tasks]
    .sort((a, b) => a.project_task_index - b.project_task_index)
    .map(
      (t) =>
        ({
          type: "Feature",
          geometry: toArea(t.outline),
          properties: { task_id: t.project_task_index },
        }) as Task,
    );
  return {
    name: project.name,
    aoi: toArea(project.outline),
    noFlyZones: project.no_fly_zones ? toArea(project.no_fly_zones) : null,
    plan: parse(makePlan(tasks, "DIVIDE_BY_SQUARE")),
  };
}
