import type { TaskStatus, TaskSummary } from "../lib/task-types";

/**
 * Canonical user-facing status labels. Raw provider strings never render
 * directly; every status shown or matched in the inbox goes through this map.
 */
export const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  queued: "Queued",
  running: "Running",
  "waiting-approval": "Waiting approval",
  completed: "Completed",
  rejected: "Rejected",
  failed: "Failed",
  cancelled: "Cancelled",
  unknown: "Unknown",
};

export const TASK_STATUS_FILTER_OPTIONS = [
  "queued",
  "running",
  "waiting-approval",
  "completed",
  "rejected",
  "failed",
  "cancelled",
  "unknown",
] as const satisfies readonly TaskStatus[];

export type TaskStatusFilter = "all" | TaskStatus;

/** Recency windows for the inbox date filter, measured against the local clock. */
export type TaskDateWindow = "any" | "24h" | "7d" | "30d";

export const TASK_DATE_WINDOW_OPTIONS = [
  "any",
  "24h",
  "7d",
  "30d",
] as const satisfies readonly TaskDateWindow[];

export const TASK_DATE_WINDOW_LABELS: Record<TaskDateWindow, string> = {
  any: "Any time",
  "24h": "Last 24 hours",
  "7d": "Last 7 days",
  "30d": "Last 30 days",
};

const DATE_WINDOW_MS: Record<Exclude<TaskDateWindow, "any">, number> = {
  "24h": 24 * 60 * 60 * 1000,
  "7d": 7 * 24 * 60 * 60 * 1000,
  "30d": 30 * 24 * 60 * 60 * 1000,
};

export interface TaskInboxFilter {
  attentionOnly: boolean;
  dateWindow: TaskDateWindow;
  query: string;
  status: TaskStatusFilter;
}

export const EMPTY_TASK_INBOX_FILTER: TaskInboxFilter = {
  attentionOnly: false,
  dateWindow: "any",
  query: "",
  status: "all",
};

export const TASK_SEARCH_MAX_LENGTH = 200;

export function normalizeTaskQuery(query: string): string {
  return query.slice(0, TASK_SEARCH_MAX_LENGTH);
}

/** A task requires attention when it is waiting on a human decision. */
export function requiresAttention(task: TaskSummary): boolean {
  return task.status === "waiting-approval";
}

/** The identifier text exactly as the inbox row renders it. */
export function taskIdentifierLabel(task: TaskSummary): string {
  return task.runId ? `Run ${task.runId.slice(0, 10)}` : `Task ${task.taskId.slice(0, 10)}`;
}

/**
 * The safe, user-visible text a row displays: title, the truncated run/task
 * identifier label, and the canonical status label. Hidden fields such as the
 * raw prompt, results, evidence, or full identifiers are deliberately excluded
 * so search never matches text the list does not show.
 */
export function visibleTaskText(task: TaskSummary): string {
  return [task.title, taskIdentifierLabel(task), TASK_STATUS_LABELS[task.status]].join("\n");
}

/**
 * Whether a task falls inside the selected recency window, measured against the
 * browser's local clock. A task with no (or unparseable) `createdAt` has no
 * known time, so it appears only under "Any time" — never silently placed in a
 * window. Future-dated tasks are likewise excluded from "last N" windows.
 */
export function matchesDateWindow(task: TaskSummary, window: TaskDateWindow, now: number): boolean {
  if (window === "any") {
    return true;
  }
  if (task.createdAt === undefined) {
    return false;
  }
  const created = Date.parse(task.createdAt);
  if (Number.isNaN(created)) {
    return false;
  }
  return created <= now && now - created <= DATE_WINDOW_MS[window];
}

export function matchesTaskFilter(
  task: TaskSummary,
  filter: TaskInboxFilter,
  now: number = Date.now(),
): boolean {
  if (filter.status !== "all" && task.status !== filter.status) {
    return false;
  }
  if (filter.attentionOnly && !requiresAttention(task)) {
    return false;
  }
  if (!matchesDateWindow(task, filter.dateWindow, now)) {
    return false;
  }
  const query = normalizeTaskQuery(filter.query).trim().toLocaleLowerCase();
  if (query === "") {
    return true;
  }
  return visibleTaskText(task).toLocaleLowerCase().includes(query);
}

export function filterTasks(
  tasks: readonly TaskSummary[],
  filter: TaskInboxFilter,
  now: number = Date.now(),
): TaskSummary[] {
  return tasks.filter((task) => matchesTaskFilter(task, filter, now));
}

export interface TaskInboxCounts {
  attention: number;
  byStatus: Record<TaskStatus, number>;
  total: number;
}

export function countTasks(tasks: readonly TaskSummary[]): TaskInboxCounts {
  const byStatus = Object.fromEntries(
    TASK_STATUS_FILTER_OPTIONS.map((status) => [status, 0]),
  ) as Record<TaskStatus, number>;
  let attention = 0;
  for (const task of tasks) {
    byStatus[task.status] += 1;
    if (requiresAttention(task)) {
      attention += 1;
    }
  }
  return { attention, byStatus, total: tasks.length };
}

export function hasActiveTaskFilter(filter: TaskInboxFilter): boolean {
  return (
    filter.query.trim() !== "" ||
    filter.status !== "all" ||
    filter.attentionOnly ||
    filter.dateWindow !== "any"
  );
}

/** Join criteria into a natural list ("a", "a and b", "a, b, and c", …). */
function joinCriteria(items: readonly string[]): string {
  if (items.length === 1) {
    return items[0];
  }
  if (items.length === 2) {
    return `${items[0]} and ${items[1]}`;
  }
  return `${items.slice(0, -1).join(", ")}, and ${items[items.length - 1]}`;
}

/**
 * A complete sentence explaining which criteria removed every result, for the
 * filtered-empty state.
 */
export function describeTaskFilter(filter: TaskInboxFilter): string {
  const criteria: string[] = [];
  const query = filter.query.trim();
  if (query !== "") {
    criteria.push(`match “${query}”`);
  }
  if (filter.status !== "all") {
    criteria.push(`have the ${TASK_STATUS_LABELS[filter.status]} status`);
  }
  if (filter.attentionOnly) {
    criteria.push("need attention");
  }
  if (filter.dateWindow !== "any") {
    criteria.push(
      `were created in the ${TASK_DATE_WINDOW_LABELS[filter.dateWindow].toLowerCase()}`,
    );
  }
  if (criteria.length === 0) {
    return "No loaded tasks match the current filters.";
  }
  return `No loaded tasks ${joinCriteria(criteria)}.`;
}
