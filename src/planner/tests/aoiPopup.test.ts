import { describe, expect, it } from "vitest";
import { aoiPopupOpen, nextAoiClick } from "../src/lib/aoiPopup";

const open = {
  readonly: false,
  step: 0,
  tool: "none",
  hasAoi: true,
  click: { n: 1, at: [85.3, 27.7] },
};

describe("aoiPopupOpen", () => {
  it("opens on the Area step after a click on the area", () => {
    expect(aoiPopupOpen(open)).toBe(true);
  });

  it.each([
    ["read-only view", { readonly: true }],
    ["another step", { step: 3 }],
    ["a drawing tool active", { tool: "polygon" }],
    ["no area", { hasAoi: false }],
    ["no click yet", { click: null }],
  ])("stays closed with %s", (_, change) => {
    expect(aoiPopupOpen({ ...open, ...change })).toBe(false);
  });
});

describe("nextAoiClick", () => {
  it("numbers each click so the popup remounts at the new spot", () => {
    expect(nextAoiClick(0, [1, 2])).toEqual({ n: 1, at: [1, 2] });
    expect(nextAoiClick(4, [3, 4])).toEqual({ n: 5, at: [3, 4] });
  });

  it("closes the popup when the click missed the area", () => {
    expect(nextAoiClick(4, null)).toBeNull();
  });
});
