import { describe, expect, it } from "vitest";
import {
  isTaskPlan,
  makePlan,
  parse,
  serialise,
  validate,
  TaskPlanError,
  type Task,
} from "../src/lib/taskPlan";

const sq = (x: number): Task["geometry"] => ({
  type: "Polygon",
  coordinates: [
    [
      [x, 0],
      [x + 1, 0],
      [x + 1, 1],
      [x, 1],
      [x, 0],
    ],
  ],
});
const task = (id: number, props: Partial<Task["properties"]> = {}): Task => ({
  type: "Feature",
  geometry: sq(id),
  properties: { task_id: id, ...props },
});

describe("validate", () => {
  it("accepts a valid plan", () => {
    expect(
      validate(makePlan([task(1, { assigned_group: "team-a_1", colour: "#d63f3f" }), task(2)])),
    ).toEqual([]);
  });

  it.each([
    ["not a collection", { type: "Feature" }, /FeatureCollection/],
    ["wrong version", { ...makePlan([task(1)]), task_plan_version: 2 }, /task_plan_version/],
    ["empty", makePlan([]), /no tasks/],
    ["bad group", makePlan([task(1, { assigned_group: "team a" })]), /assigned_group/],
    ["bad colour", makePlan([task(1, { colour: "red" })]), /colour/],
    ["duplicate ids", makePlan([task(1), task(1)]), /duplicate/],
    ["gaps in ids", makePlan([task(1), task(3)]), /1\.\.n/],
    ["non-integer id", makePlan([task(1.5)]), /task_id/],
    [
      "multipolygon",
      makePlan([{ ...task(1), geometry: { type: "MultiPolygon", coordinates: [] } as never }]),
      /Polygon/,
    ],
    [
      "open ring",
      makePlan([
        {
          ...task(1),
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                [0, 0],
                [1, 1],
              ],
            ],
          },
        },
      ]),
      /Polygon/,
    ],
  ])("rejects %s", (_, input, msg) => {
    expect(validate(input).join("\n")).toMatch(msg);
  });
});

describe("parse / serialise", () => {
  it("round-trips and drops empty optional fields", () => {
    const plan = makePlan(
      [task(1, { assigned_to: "  ", comment: "Start Monday" })],
      "DIVIDE_BY_SQUARE",
      { cell_size: 100 },
    );
    const out = JSON.parse(serialise(plan));
    expect(out.task_plan_version).toBe(1);
    expect(out.params).toEqual({ cell_size: 100 });
    expect(out.features[0].properties).toEqual({ task_id: 1, comment: "Start Monday" });
    expect(parse(out).features).toHaveLength(1);
  });

  it("fills in missing task ids, version and single-part multipolygons", () => {
    const plan = parse({
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          geometry: { type: "MultiPolygon", coordinates: [sq(0).coordinates] },
          properties: {},
        },
        { type: "Feature", geometry: sq(1), properties: null },
      ],
    });
    expect(plan.features.map((f) => f.properties.task_id)).toEqual([1, 2]);
    expect(plan.features[0].geometry.type).toBe("Polygon");
    expect(plan.algorithm).toBe("MANUAL");
  });

  it("throws TaskPlanError with all problems", () => {
    expect(() => parse('{"type":"FeatureCollection","features":[]}')).toThrow(TaskPlanError);
    expect(() => serialise(makePlan([task(1, { assigned_group: "a b" })]))).toThrow(
      /assigned_group/,
    );
  });
});

describe("importing a task plan", () => {
  const tasks: Task[] = [
    {
      type: "Feature",
      geometry: sq(0),
      properties: { task_id: 1, assigned_group: "north", comment: "Start here", feature_count: 4 },
    },
    { type: "Feature", geometry: sq(1), properties: { task_id: 2, assigned_to: "Chomba" } },
  ];

  it("round-trips an exported plan with its assignments", () => {
    const json = JSON.parse(
      serialise(makePlan(tasks, "AVG_BUILDING_VORONOI", { num_buildings: 10 })),
    );
    expect(isTaskPlan(json)).toBe(true);
    const plan = parse(json);
    expect(plan.features.map((f) => f.properties)).toEqual(tasks.map((t) => t.properties));
    expect(plan.algorithm).toBe("AVG_BUILDING_VORONOI");
  });

  it("detects plans without task_plan_version by their task ids", () => {
    expect(isTaskPlan({ type: "FeatureCollection", features: tasks })).toBe(true);
  });

  it("treats plain polygons as an area, not a plan", () => {
    const area = {
      type: "FeatureCollection",
      features: [{ type: "Feature", geometry: sq(0), properties: {} }],
    };
    expect(isTaskPlan(area)).toBe(false);
  });
});
