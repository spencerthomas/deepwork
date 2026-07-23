import { describe, expect, it } from "vitest";

import { INBOX_GROUP_ORDER, moveInboxFocus, orderedInboxIds } from "./task-inbox-navigation";
import type { TaskStatus, TaskSummary } from "../../lib/task-types";

function task(taskId: string, status: TaskStatus): TaskSummary {
  return { taskId, title: taskId, status };
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
