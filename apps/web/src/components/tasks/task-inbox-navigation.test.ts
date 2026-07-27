import { describe, expect, it } from "vitest";

import {
  INBOX_GROUP_ORDER,
  moveInboxFocus,
  orderedInboxIds,
  sortTasksByRecency,
} from "./task-inbox-navigation";
import type { TaskStatus, TaskSummary } from "../../lib/task-types";

function task(taskId: string, status: TaskStatus): TaskSummary {
  return { taskId, title: taskId, status };
}

function createdTask(taskId: string, createdAt: string | undefined): TaskSummary {
  return {
    taskId,
    title: taskId,
    status: "queued",
    ...(createdAt === undefined ? {} : { createdAt }),
  };
}

const mixed: TaskSummary[] = [
  task("t_done", "completed"),
  task("t_review", "waiting-approval"),
  task("t_run", "running"),
  task("t_done2", "completed"),
];

describe("orderedInboxIds", () => {
  it("walks the group order in grouped-all view, not the raw list order", () => {
    expect(orderedInboxIds(mixed, true, "all")).toEqual(["t_review", "t_run", "t_done", "t_done2"]);
  });

  it("keeps the filtered order for the recent (ungrouped) view", () => {
    expect(orderedInboxIds(mixed, false, "all")).toEqual([
      "t_done",
      "t_review",
      "t_run",
      "t_done2",
    ]);
  });

  it("keeps list order when a single status is selected even if grouped is on", () => {
    // The inbox passes an already status-filtered list here, so grouping must
    // not re-sort it — the rows show in the order the caller provides.
    const completed = mixed.filter((t) => t.status === "completed");
    expect(orderedInboxIds(completed, true, "completed")).toEqual(["t_done", "t_done2"]);
  });

  it("covers every task status so grouping never silently drops a row", () => {
    expect([...INBOX_GROUP_ORDER].sort()).toEqual([...new Set(INBOX_GROUP_ORDER)].sort());
    expect(INBOX_GROUP_ORDER).toContain("unknown");
  });
});

describe("sortTasksByRecency", () => {
  it("orders the newest-created task first", () => {
    const ordered = sortTasksByRecency([
      createdTask("oldest", "2026-07-20T08:00:00Z"),
      createdTask("newest", "2026-07-24T08:00:00Z"),
      createdTask("middle", "2026-07-22T08:00:00Z"),
    ]);
    expect(ordered.map((t) => t.taskId)).toEqual(["newest", "middle", "oldest"]);
  });

  it("sinks tasks with an unknown or unparseable creation time to the bottom", () => {
    const ordered = sortTasksByRecency([
      createdTask("unknown", undefined),
      createdTask("real", "2026-07-24T08:00:00Z"),
      createdTask("bad", "not-a-date"),
    ]);
    expect(ordered[0]?.taskId).toBe("real");
    expect(
      ordered
        .slice(1)
        .map((t) => t.taskId)
        .sort(),
    ).toEqual(["bad", "unknown"]);
  });

  it("is stable for equal timestamps and does not mutate the input", () => {
    const input = [
      createdTask("first", "2026-07-24T08:00:00Z"),
      createdTask("second", "2026-07-24T08:00:00Z"),
      createdTask("third", "2026-07-24T08:00:00Z"),
    ];
    const ordered = sortTasksByRecency(input);
    expect(ordered.map((t) => t.taskId)).toEqual(["first", "second", "third"]);
    expect(input.map((t) => t.taskId)).toEqual(["first", "second", "third"]);
    expect(ordered).not.toBe(input);
  });
});

describe("moveInboxFocus", () => {
  const ids = ["a", "b", "c"];

  it("lands on the first row moving down from nothing and the last moving up", () => {
    expect(moveInboxFocus(null, ids, 1)).toBe("a");
    expect(moveInboxFocus(null, ids, -1)).toBe("c");
  });

  it("steps one row and clamps at both ends without wrapping", () => {
    expect(moveInboxFocus("a", ids, 1)).toBe("b");
    expect(moveInboxFocus("c", ids, 1)).toBe("c");
    expect(moveInboxFocus("a", ids, -1)).toBe("a");
  });

  it("recovers to an end when the highlighted row is no longer present", () => {
    expect(moveInboxFocus("gone", ids, 1)).toBe("a");
    expect(moveInboxFocus("gone", ids, -1)).toBe("c");
  });

  it("returns null when there is nothing to highlight", () => {
    expect(moveInboxFocus(null, [], 1)).toBeNull();
    expect(moveInboxFocus("a", [], -1)).toBeNull();
  });
});
