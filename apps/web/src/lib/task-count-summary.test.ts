import { describe, expect, it } from "vitest";

import { describeTaskCounts, summarizeTasks } from "./task-count-summary";
import type { TaskStatus, TaskSummary } from "./task-types";

function task(status: TaskStatus): TaskSummary {
  return { taskId: "task_00000001", title: "A task", status };
}

describe("summarizeTasks", () => {
  it("counts the total and the actionable end states", () => {
    const summary = summarizeTasks([
      task("waiting-approval"),
      task("waiting-approval"),
      task("completed"),
      task("running"),
      task("queued"),
    ]);
    expect(summary).toEqual({ total: 5, awaitingApproval: 2, completed: 1 });
  });

  it("reports all zeros for an empty session", () => {
    expect(summarizeTasks([])).toEqual({ total: 0, awaitingApproval: 0, completed: 0 });
  });
});

describe("describeTaskCounts", () => {
  it("states the total and omits zero clauses", () => {
    expect(describeTaskCounts({ total: 5, awaitingApproval: 2, completed: 1 })).toBe(
      "5 tasks · 2 awaiting approval · 1 completed",
    );
    expect(describeTaskCounts({ total: 3, awaitingApproval: 0, completed: 0 })).toBe("3 tasks");
    expect(describeTaskCounts({ total: 1, awaitingApproval: 0, completed: 1 })).toBe(
      "1 task · 1 completed",
    );
  });

  it("returns undefined when there is nothing to describe", () => {
    expect(describeTaskCounts({ total: 0, awaitingApproval: 0, completed: 0 })).toBeUndefined();
  });
});
