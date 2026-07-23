import { describe, expect, it } from "vitest";

import {
  buildCommandResults,
  ROUTE_COMMANDS,
  routeCommands,
  TASK_RESULT_LIMIT,
  taskCommandItem,
} from "./command-palette-model";
import type { TaskSummary } from "../../lib/task-types";

function task(id: string, title: string, runId?: string): TaskSummary {
  return { taskId: id, title, status: "running", ...(runId ? { runId } : {}) };
}

const tasks: TaskSummary[] = [
  task("task_00000001", "Refresh the billing summary", "run_00000001"),
  task("task_00000002", "Draft the release notes", "run_00000002"),
  task("task_00000003", "Archive stale sandboxes"),
];

describe("buildCommandResults", () => {
  it("shows only route commands when the query is empty", () => {
    const results = buildCommandResults("", tasks);
    expect(results).toHaveLength(ROUTE_COMMANDS.length);
    expect(results.every((item) => item.id.startsWith("route:"))).toBe(true);
  });

  it("surfaces matching loaded tasks once the user types", () => {
    const results = buildCommandResults("billing", tasks);
    const taskResults = results.filter((item) => item.id.startsWith("task:"));
    expect(taskResults).toHaveLength(1);
    expect(taskResults[0]).toMatchObject({
      id: "task:task_00000001",
      label: "Refresh the billing summary",
      href: "/tasks/task_00000001",
      icon: "task",
    });
  });

  it("still filters route commands by the query", () => {
    const results = buildCommandResults("approvals", tasks);
    expect(results.some((item) => item.id === "route:approvals")).toBe(true);
    expect(results.some((item) => item.id === "route:agents")).toBe(false);
  });

  it("keeps the new-task hint mode-aware without inferring an API runner", () => {
    const apiHint = routeCommands("api").find((item) => item.id === "route:new")?.hint;
    const fixtureHint = routeCommands("fixture").find((item) => item.id === "route:new")?.hint;

    expect(apiHint).toBe("Dispatch through the configured API");
    expect(apiHint).not.toMatch(/local|runner|deterministic/i);
    expect(fixtureHint).toBe("Dispatch the in-browser fixture runner");
  });

  it("matches the task title case-insensitively and ignores surrounding space", () => {
    expect(
      buildCommandResults("  RELEASE ", tasks).some((i) => i.id === "task:task_00000002"),
    ).toBe(true);
  });

  it("caps the number of task results", () => {
    const many = Array.from({ length: 20 }, (_, i) =>
      task(`task_${String(i).padStart(8, "0")}`, "shared token"),
    );
    const results = buildCommandResults("shared", many, TASK_RESULT_LIMIT);
    expect(results.filter((item) => item.id.startsWith("task:"))).toHaveLength(TASK_RESULT_LIMIT);
  });

  it("labels the task row with its visible identifier, not hidden fields", () => {
    expect(taskCommandItem(tasks[0]).hint).toBe("Open task · Run run_000000");
    expect(taskCommandItem(tasks[2]).hint).toBe("Open task · Task task_00000");
  });
});
