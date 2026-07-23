import { describe, expect, it } from "vitest";

import { activityTimestamp, describeActivityTime, sortByRecency } from "./activity-feed";
import type { TaskSummary } from "../lib/task-types";

function task(
  taskId: string,
  times: Partial<Pick<TaskSummary, "createdAt" | "updatedAt">>,
): TaskSummary {
  return { taskId, title: `Task ${taskId}`, status: "running", ...times };
}

describe("activityTimestamp", () => {
  it("prefers updatedAt over createdAt", () => {
    expect(
      activityTimestamp(
        task("t", { createdAt: "2026-07-20T00:00:00Z", updatedAt: "2026-07-22T00:00:00Z" }),
      ),
    ).toBe("2026-07-22T00:00:00Z");
  });

  it("falls back to createdAt when there is no update", () => {
    expect(activityTimestamp(task("t", { createdAt: "2026-07-20T00:00:00Z" }))).toBe(
      "2026-07-20T00:00:00Z",
    );
  });

  it("is undefined when a task carries no timestamps", () => {
    expect(activityTimestamp(task("t", {}))).toBeUndefined();
  });
});

describe("sortByRecency", () => {
  it("orders tasks newest activity first", () => {
    const tasks = [
      task("older", { updatedAt: "2026-07-21T10:00:00Z" }),
      task("newest", { updatedAt: "2026-07-23T10:00:00Z" }),
      task("middle", { updatedAt: "2026-07-22T10:00:00Z" }),
    ];

    expect(sortByRecency(tasks).map((entry) => entry.taskId)).toEqual([
      "newest",
      "middle",
      "older",
    ]);
  });

  it("compares against createdAt when updatedAt is missing", () => {
    const tasks = [
      task("a", { createdAt: "2026-07-20T00:00:00Z" }),
      task("b", { updatedAt: "2026-07-23T00:00:00Z" }),
    ];

    expect(sortByRecency(tasks).map((entry) => entry.taskId)).toEqual(["b", "a"]);
  });

  it("places undated tasks last while preserving their input order", () => {
    const tasks = [
      task("undated-first", {}),
      task("dated", { updatedAt: "2026-07-23T00:00:00Z" }),
      task("undated-second", {}),
    ];

    expect(sortByRecency(tasks).map((entry) => entry.taskId)).toEqual([
      "dated",
      "undated-first",
      "undated-second",
    ]);
  });

  it("does not mutate the input array", () => {
    const tasks = [
      task("a", { updatedAt: "2026-07-21T00:00:00Z" }),
      task("b", { updatedAt: "2026-07-23T00:00:00Z" }),
    ];
    const original = tasks.map((entry) => entry.taskId);

    sortByRecency(tasks);

    expect(tasks.map((entry) => entry.taskId)).toEqual(original);
  });
});

describe("describeActivityTime", () => {
  it("labels a missing timestamp as unavailable", () => {
    expect(describeActivityTime(undefined)).toBe("Time unavailable");
  });

  it("labels an unparseable timestamp as unavailable", () => {
    expect(describeActivityTime("not-a-date")).toBe("Time unavailable");
  });

  it("renders a non-empty label for a valid timestamp", () => {
    expect(describeActivityTime("2026-07-23T10:00:00Z")).not.toBe("Time unavailable");
  });
});
