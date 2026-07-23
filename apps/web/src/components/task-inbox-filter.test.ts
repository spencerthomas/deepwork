import { describe, expect, it } from "vitest";

import {
  EMPTY_TASK_INBOX_FILTER,
  TASK_SEARCH_MAX_LENGTH,
  TASK_STATUS_FILTER_OPTIONS,
  countTasks,
  describeTaskFilter,
  filterTasks,
  hasActiveTaskFilter,
  matchesTaskFilter,
  normalizeTaskQuery,
  requiresAttention,
  taskIdentifierLabel,
  visibleTaskText,
  type TaskInboxFilter,
} from "./task-inbox-filter";
import type { TaskSummary } from "../lib/task-types";

const waiting: TaskSummary = {
  taskId: "fixture-task-1",
  runId: "fixture-run-1",
  title: "Refresh the billing summary",
  prompt: "Refresh the billing summary",
  status: "waiting-approval",
};

const running: TaskSummary = {
  taskId: "fixture-task-2",
  runId: "fixture-run-2",
  title: "Draft the release notes",
  prompt: "hidden-prompt-marker draft everything",
  status: "running",
};

const completed: TaskSummary = {
  taskId: "fixture-task-3",
  title: "Archive stale sandboxes",
  status: "completed",
};

const tasks = [waiting, running, completed];

function filterWith(overrides: Partial<TaskInboxFilter>): TaskInboxFilter {
  return { ...EMPTY_TASK_INBOX_FILTER, ...overrides };
}

describe("task inbox search", () => {
  it("matches the task title case-insensitively and ignores surrounding spaces", () => {
    expect(matchesTaskFilter(waiting, filterWith({ query: "  BILLING  " }))).toBe(true);
    expect(matchesTaskFilter(running, filterWith({ query: "billing" }))).toBe(false);
  });

  it("matches only the identifier text that the row actually displays", () => {
    expect(taskIdentifierLabel(running)).toBe("Run fixture-ru");
    expect(taskIdentifierLabel(completed)).toBe("Task fixture-ta");
    expect(matchesTaskFilter(running, filterWith({ query: "run fixture-ru" }))).toBe(true);
    expect(matchesTaskFilter(running, filterWith({ query: "fixture-run-2" }))).toBe(false);
  });

  it("matches the canonical status label shown on the row", () => {
    expect(matchesTaskFilter(waiting, filterWith({ query: "waiting approval" }))).toBe(true);
    expect(matchesTaskFilter(running, filterWith({ query: "waiting approval" }))).toBe(false);
  });

  it("never searches hidden fields such as the raw prompt", () => {
    expect(visibleTaskText(running)).not.toContain("hidden-prompt-marker");
    expect(matchesTaskFilter(running, filterWith({ query: "hidden-prompt-marker" }))).toBe(false);
  });

  it("bounds the query length", () => {
    expect(normalizeTaskQuery("a".repeat(TASK_SEARCH_MAX_LENGTH + 50))).toHaveLength(
      TASK_SEARCH_MAX_LENGTH,
    );
  });
});

describe("task inbox status and attention filters", () => {
  it("filters by canonical user-facing status", () => {
    expect(filterTasks(tasks, filterWith({ status: "running" }))).toEqual([running]);
    expect(filterTasks(tasks, filterWith({ status: "failed" }))).toEqual([]);
  });

  it("treats waiting-approval as the attention-required state", () => {
    expect(requiresAttention(waiting)).toBe(true);
    expect(requiresAttention(running)).toBe(false);
    expect(filterTasks(tasks, filterWith({ attentionOnly: true }))).toEqual([waiting]);
  });

  it("combines search, status, and attention criteria", () => {
    expect(filterTasks(tasks, filterWith({ query: "billing", attentionOnly: true }))).toEqual([
      waiting,
    ]);
    expect(filterTasks(tasks, filterWith({ query: "billing", status: "completed" }))).toEqual([]);
  });

  it("counts every canonical status and the attention total", () => {
    const counts = countTasks(tasks);
    expect(counts.total).toBe(3);
    expect(counts.attention).toBe(1);
    expect(counts.byStatus["waiting-approval"]).toBe(1);
    expect(counts.byStatus.running).toBe(1);
    expect(counts.byStatus.completed).toBe(1);
    expect(counts.byStatus.failed).toBe(0);
    expect(Object.keys(counts.byStatus)).toHaveLength(TASK_STATUS_FILTER_OPTIONS.length);
  });
});

describe("task inbox filter state helpers", () => {
  it("reports whether any filter is active", () => {
    expect(hasActiveTaskFilter(EMPTY_TASK_INBOX_FILTER)).toBe(false);
    expect(hasActiveTaskFilter(filterWith({ query: "   " }))).toBe(false);
    expect(hasActiveTaskFilter(filterWith({ query: "x" }))).toBe(true);
    expect(hasActiveTaskFilter(filterWith({ status: "queued" }))).toBe(true);
    expect(hasActiveTaskFilter(filterWith({ attentionOnly: true }))).toBe(true);
  });

  it("explains exactly which criteria removed every result", () => {
    expect(describeTaskFilter(filterWith({ query: "deploy" }))).toBe(
      "No loaded tasks match “deploy”.",
    );
    expect(describeTaskFilter(filterWith({ status: "running", attentionOnly: true }))).toBe(
      "No loaded tasks have the Running status and need attention.",
    );
    expect(
      describeTaskFilter(filterWith({ query: "deploy", status: "failed", attentionOnly: true })),
    ).toBe("No loaded tasks match “deploy”, have the Failed status, and need attention.");
  });
});
