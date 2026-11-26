import type { Position } from "geojson";

export interface AoiClick {
  /** Increases on every click, so the popup remounts at the new spot. */
  n: number;
  at: Position;
}

/** The area popup shows on the Area step, with no drawing tool active, after a click on the area. */
export function aoiPopupOpen(s: {
  readonly: boolean;
  step: number;
  tool: string;
  hasAoi: boolean;
  click: AoiClick | null;
}): boolean {
  return !s.readonly && s.step === 0 && s.tool === "none" && s.hasAoi && s.click !== null;
}

/** A click on the area opens the popup there; a click that missed it closes the popup. */
export function nextAoiClick(previous: number, at: Position | null): AoiClick | null {
  return at ? { n: previous + 1, at } : null;
}
