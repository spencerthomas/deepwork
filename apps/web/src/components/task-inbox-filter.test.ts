import { describe, expect, it } from "vitest";

import {
  EMPTY_TASK_INBOX_FILTER,
  TASK_SEARCH_MAX_LENGTH,
  TASK_STATUS_FILTER_OPTIONS,
  countTasks,
  describeTaskFilter,
  filterTasks,
  hasActiveTaskFilter,
  matchesDateWindow,
  matchesTaskFilter,
  normalizeTaskQuery,
  requiresAttention,
  taskIdentifierLabel,
  visibleTaskText,
  type TaskInboxFilter,
} from "./task-inbox-filter";
import type { TaskSummary } from "../lib/task-types";

const NOW = Date.parse("2026-07-24T12:00:00.000Z");
const HOUR = 60 * 60 * 1000;
const DAY = 24 * HOUR;
const at = (offsetMs: number): string => new Date(NOW - offsetMs).toISOString();

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

describe("task inbox date window filter", () => {
  const recent: TaskSummary = {
    taskId: "t-recent",
    title: "Recent",
    status: "completed",
    createdAt: at(2 * HOUR),
  };
  const lastWeek: TaskSummary = {
    taskId: "t-week",
    title: "This week",
    status: "completed",
    createdAt: at(3 * DAY),
  };
  const old: TaskSummary = {
    taskId: "t-old",
    title: "Old",
    status: "completed",
    createdAt: at(40 * DAY),
  };
  const undated: TaskSummary = { taskId: "t-undated", title: "Undated", status: "completed" };
  const future: TaskSummary = {
    taskId: "t-future",
    title: "Future",
    status: "completed",
    createdAt: at(-2 * HOUR),
  };
  const dated = [recent, lastWeek, old, undated, future];

  it("keeps everything under the 'any' window", () => {
    expect(matchesDateWindow(old, "any", NOW)).toBe(true);
    expect(matchesDateWindow(undated, "any", NOW)).toBe(true);
    expect(filterTasks(dated, filterWith({ dateWindow: "any" }), NOW)).toEqual(dated);
  });

  it("keeps only tasks inside the selected window", () => {
    expect(filterTasks(dated, filterWith({ dateWindow: "24h" }), NOW)).toEqual([recent]);
    expect(filterTasks(dated, filterWith({ dateWindow: "7d" }), NOW)).toEqual([recent, lastWeek]);
    expect(filterTasks(dated, filterWith({ dateWindow: "30d" }), NOW)).toEqual([recent, lastWeek]);
  });

  it("includes the exact window boundary", () => {
    const edge: TaskSummary = {
      taskId: "edge",
      title: "Edge",
      status: "completed",
      createdAt: at(7 * DAY),
    };
    expect(matchesDateWindow(edge, "7d", NOW)).toBe(true);
  });

  it("shows timestamp-less and future-dated tasks only under 'any'", () => {
    expect(matchesDateWindow(undated, "7d", NOW)).toBe(false);
    expect(matchesDateWindow(future, "24h", NOW)).toBe(false);
    expect(matchesDateWindow({ ...undated, createdAt: "not-a-date" }, "7d", NOW)).toBe(false);
  });

  it("combines with other criteria", () => {
    expect(filterTasks(dated, filterWith({ dateWindow: "7d", query: "recent" }), NOW)).toEqual([
      recent,
    ]);
  });
});

describe("task inbox filter state helpers", () => {
  it("reports whether any filter is active", () => {
    expect(hasActiveTaskFilter(EMPTY_TASK_INBOX_FILTER)).toBe(false);
    expect(hasActiveTaskFilter(filterWith({ query: "   " }))).toBe(false);
    expect(hasActiveTaskFilter(filterWith({ query: "x" }))).toBe(true);
    expect(hasActiveTaskFilter(filterWith({ status: "queued" }))).toBe(true);
    expect(hasActiveTaskFilter(filterWith({ attentionOnly: true }))).toBe(true);
    expect(hasActiveTaskFilter(filterWith({ dateWindow: "7d" }))).toBe(true);
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

  it("names the date window and joins four criteria naturally", () => {
    expect(describeTaskFilter(filterWith({ dateWindow: "7d" }))).toBe(
      "No loaded tasks were created in the last 7 days.",
    );
    expect(
      describeTaskFilter(
        filterWith({ query: "deploy", status: "failed", attentionOnly: true, dateWindow: "24h" }),
      ),
    ).toBe(
      "No loaded tasks match “deploy”, have the Failed status, need attention, and were created in the last 24 hours.",
    );
  });
});
