import { describe, expect, it } from "vitest";
import { History } from "../src/lib/history";

describe("History", () => {
  it("undoes and redoes", () => {
    const h = new History(0);
    h.push(1);
    h.push(2);
    expect(h.undo()).toBe(1);
    expect(h.undo()).toBe(0);
    expect(h.canUndo).toBe(false);
    expect(h.undo()).toBe(0);
    expect(h.redo()).toBe(1);
    expect(h.canRedo).toBe(true);
  });

  it("drops the redo stack on a new change and respects the limit", () => {
    const h = new History(0, 2);
    h.push(1);
    h.undo();
    h.push(5);
    expect(h.canRedo).toBe(false);
    h.push(6);
    h.push(7);
    expect(h.undo()).toBe(6);
    expect(h.undo()).toBe(5);
    expect(h.canUndo).toBe(false);
  });

  it("reset clears history", () => {
    const h = new History("a");
    h.push("b");
    h.reset("c");
    expect([h.present, h.canUndo, h.canRedo]).toEqual(["c", false, false]);
  });
});
