import type { FeatureCollection } from "geojson";
import type { Area } from "./geo";
import type { TaskPlan } from "./taskPlan";

export interface Draft {
  aoi: Area | null;
  features: FeatureCollection | null;
  roads: FeatureCollection | null;
  plan: TaskPlan | null;
  savedAt: string;
}

const key = (scope: string) => `field-tm-planner:draft:${scope}`;

/** Best effort: drops input data if the plan alone fits in storage. */
export function saveDraft(scope: string, d: Omit<Draft, "savedAt">): boolean {
  const savedAt = new Date().toISOString();
  for (const draft of [
    { ...d, savedAt },
    { ...d, features: null, roads: null, savedAt },
  ]) {
    try {
      localStorage.setItem(key(scope), JSON.stringify(draft));
      return true;
    } catch {
      /* quota exceeded or storage blocked */
    }
  }
  return false;
}

export function loadDraft(scope: string): Draft | null {
  try {
    const s = localStorage.getItem(key(scope));
    return s ? (JSON.parse(s) as Draft) : null;
  } catch {
    return null;
  }
}

export function clearDraft(scope: string) {
  try {
    localStorage.removeItem(key(scope));
  } catch {
    /* ignore */
  }
}
