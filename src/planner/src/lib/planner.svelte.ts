import type { FeatureCollection, LineString, Polygon } from "geojson";
import { engine } from "./engine/client";
import type { SplitAlgorithm, SplitParams } from "./engine/splitter";
import { saveDraft, type Draft } from "./draft";
import type { Area } from "./geo";
import { History } from "./history";
import { assign, removeTasks, replaceTasks, type Assignment } from "./planEdit";
import { makePlan, type Task, type TaskPlan } from "./taskPlan";

interface Snapshot {
  aoi: Area | null;
  tasks: Task[];
  algorithm: string;
  params: Record<string, unknown>;
}

/** Reactive planner state. Geometry work is delegated to the engine worker. */
export class Planner {
  aoi = $state.raw<Area | null>(null);
  tasks = $state.raw<Task[]>([]);
  algorithm = $state("MANUAL");
  params = $state.raw<Record<string, unknown>>({});
  features = $state.raw<FeatureCollection | null>(null);
  roads = $state.raw<FeatureCollection | null>(null);
  selected = $state<number[]>([]);
  busy = $state<string | null>(null);
  error = $state<string | null>(null);
  canUndo = $state(false);
  canRedo = $state(false);
  /** Changes since the last download or save. */
  unsaved = $state(false);
  draftSavedAt = $state<string | null>(null);
  /** Bumped when the map should zoom to the data. */
  fitKey = $state(0);

  #history: History<Snapshot>;
  #saveTimer: ReturnType<typeof setTimeout> | undefined;

  constructor(public scope: string) {
    this.#history = new History(this.#snapshot());
  }

  get plan(): TaskPlan {
    return makePlan(this.tasks, this.algorithm, this.params);
  }

  get selectedTasks(): Task[] {
    return this.tasks.filter((t) => this.selected.includes(t.properties.task_id));
  }

  #snapshot(): Snapshot {
    return { aoi: this.aoi, tasks: this.tasks, algorithm: this.algorithm, params: this.params };
  }

  #apply(s: Snapshot) {
    this.aoi = s.aoi;
    this.tasks = s.tasks;
    this.algorithm = s.algorithm;
    this.params = s.params;
    const ids = new Set(s.tasks.map((t) => t.properties.task_id));
    this.selected = this.selected.filter((id) => ids.has(id));
    this.canUndo = this.#history.canUndo;
    this.canRedo = this.#history.canRedo;
  }

  commit(changes: Partial<Snapshot>, select?: number[]) {
    const next = { ...this.#snapshot(), ...changes };
    this.#history.push(next);
    if (select) this.selected = select;
    this.#apply(next);
    this.unsaved = true;
    this.#autosave();
  }

  /** Replace everything without an undo step (initial load, restore draft). */
  load(d: Partial<Draft> & { algorithm?: string; params?: Record<string, unknown> }) {
    this.features = d.features ?? null;
    this.roads = d.roads ?? null;
    const s: Snapshot = {
      aoi: d.aoi ?? null,
      tasks: d.plan?.features ?? [],
      algorithm: d.plan?.algorithm ?? d.algorithm ?? "MANUAL",
      params: d.plan?.params ?? d.params ?? {},
    };
    this.#history.reset(s);
    this.selected = [];
    this.#apply(s);
    this.fitKey++;
  }

  setData(kind: "features" | "roads", fc: FeatureCollection | null) {
    this[kind] = fc;
    this.#autosave();
  }

  undo() {
    this.#apply(this.#history.undo());
    this.#autosave();
  }

  redo() {
    this.#apply(this.#history.redo());
    this.#autosave();
  }

  #autosave() {
    clearTimeout(this.#saveTimer);
    this.#saveTimer = setTimeout(() => {
      const ok = saveDraft(this.scope, {
        aoi: this.aoi,
        features: this.features,
        roads: this.roads,
        plan: this.tasks.length ? this.plan : null,
      });
      if (ok) this.draftSavedAt = new Date().toLocaleTimeString();
    }, 800);
  }

  async run<T>(
    label: string,
    fn: (progress: (m: string) => void) => Promise<T>,
  ): Promise<T | undefined> {
    this.busy = label;
    this.error = null;
    try {
      return await fn((m) => (this.busy = m));
    } catch (e) {
      this.error = e instanceof Error ? e.message : String(e);
    } finally {
      this.busy = null;
    }
  }

  async split(algorithm: SplitAlgorithm, params: SplitParams) {
    const aoi = this.aoi;
    if (!aoi) return;
    const tasks = await this.run("Splitting", (p) =>
      engine.split({ aoi, algorithm, params, features: this.features, roads: this.roads }, p),
    );
    if (tasks) this.commit({ tasks, algorithm, params: { ...params } }, []);
  }

  /** Re-split only the selected tasks, keeping the rest. */
  async resplitSelected(algorithm: SplitAlgorithm, params: SplitParams) {
    const sel = this.selectedTasks;
    if (!sel.length) return;
    const aoi: Area =
      sel.length === 1
        ? sel[0].geometry
        : { type: "MultiPolygon", coordinates: sel.map((t) => t.geometry.coordinates) };
    const parts = await this.run("Splitting", (p) =>
      engine.split({ aoi, algorithm, params, features: this.features, roads: this.roads }, p),
    );
    if (!parts) return;
    const ids = sel.map((t) => t.properties.task_id);
    const first = Math.min(...ids);
    const tasks = replaceTasks(
      this.tasks,
      ids,
      parts.map((t) => t.geometry),
      parts.map((t) => t.properties.building_count ?? 0),
    );
    this.commit(
      { tasks, algorithm: "MANUAL" },
      parts.map((_, i) => first + i),
    );
  }

  async mergeSelected() {
    const sel = this.selectedTasks;
    if (sel.length < 2) return;
    const g = await this.run("Merging", () => engine.merge(sel.map((t) => t.geometry)));
    if (!g) return;
    const ids = sel.map((t) => t.properties.task_id);
    const counts = sel.every((t) => typeof t.properties.building_count === "number")
      ? [sel.reduce((s, t) => s + (t.properties.building_count ?? 0), 0)]
      : undefined;
    const tasks = replaceTasks(this.tasks, ids, [g], counts);
    this.commit({ tasks, algorithm: "MANUAL" }, [Math.min(...ids)]);
  }

  async splitSelectedByLine(line: LineString) {
    const [t] = this.selectedTasks;
    if (!t) return;
    const parts = await this.run("Splitting task", () => engine.splitByLine(t.geometry, line));
    if (!parts) return;
    const id = t.properties.task_id;
    this.commit(
      { tasks: replaceTasks(this.tasks, [id], parts), algorithm: "MANUAL" },
      parts.map((_, i) => id + i),
    );
  }

  updateGeometry(id: number, geometry: Polygon) {
    this.commit({ tasks: replaceTasks(this.tasks, [id], [geometry]), algorithm: "MANUAL" }, [id]);
  }

  deleteSelected() {
    this.commit({ tasks: removeTasks(this.tasks, this.selected), algorithm: "MANUAL" }, []);
  }

  assignSelected(patch: Assignment) {
    this.commit({ tasks: assign(this.tasks, this.selected, patch) });
  }

  toggleSelect(id: number, additive: boolean) {
    if (!additive)
      this.selected = this.selected.length === 1 && this.selected[0] === id ? [] : [id];
    else
      this.selected = this.selected.includes(id)
        ? this.selected.filter((s) => s !== id)
        : [...this.selected, id];
  }
}
