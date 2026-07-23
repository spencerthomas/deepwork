import { describe, expect, it } from "vitest";

import { selectApprovals } from "./approvals-inbox";
import type { TaskSummary } from "../lib/task-types";

function task(taskId: string, status: TaskSummary["status"]): TaskSummary {
  return { taskId, title: `Task ${taskId}`, status };
}

describe("selectApprovals", () => {
  it("keeps only tasks waiting on a human decision", () => {
    const tasks = [
      task("t1", "running"),
      task("t2", "waiting-approval"),
      task("t3", "completed"),
      task("t4", "waiting-approval"),
      task("t5", "failed"),
    ];

    expect(selectApprovals(tasks).map((entry) => entry.taskId)).toEqual(["t2", "t4"]);
  });

  it("preserves the source ordering of the loaded tasks", () => {
    const tasks = [task("late", "waiting-approval"), task("early", "waiting-approval")];

    expect(selectApprovals(tasks).map((entry) => entry.taskId)).toEqual(["late", "early"]);
  });

  it("returns an empty queue when nothing awaits approval", () => {
    const tasks = [task("t1", "running"), task("t2", "completed"), task("t3", "cancelled")];

    expect(selectApprovals(tasks)).toEqual([]);
  });
});
