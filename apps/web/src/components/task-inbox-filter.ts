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

/** Rolling "created within" windows for the inbox date filter. */
export type TaskDateWindow = "24h" | "7d" | "30d";

export const TASK_DATE_WINDOW_OPTIONS = ["24h", "7d", "30d"] as const satisfies readonly [
  TaskDateWindow,
  ...TaskDateWindow[],
];

export const TASK_DATE_WINDOW_LABELS: Record<TaskDateWindow, string> = {
  "24h": "Last 24 hours",
  "7d": "Last 7 days",
  "30d": "Last 30 days",
};

const DAY_MS = 24 * 60 * 60 * 1000;

const TASK_DATE_WINDOW_MS: Record<TaskDateWindow, number> = {
  "24h": DAY_MS,
  "7d": 7 * DAY_MS,
  "30d": 30 * DAY_MS,
};

export interface TaskInboxFilter {
  attentionOnly: boolean;
  query: string;
  status: TaskStatusFilter;
  /** When set, keep only tasks created within this rolling window. */
  createdWithin?: TaskDateWindow;
}

export const EMPTY_TASK_INBOX_FILTER: TaskInboxFilter = {
  attentionOnly: false,
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
 * True when the task's real creation instant falls inside the rolling window.
 * A task whose creation time is unknown or unparseable fails closed (excluded)
 * rather than being assumed recent — the filter never fabricates a date.
 */
function isWithinDateWindow(task: TaskSummary, window: TaskDateWindow, now: number): boolean {
  if (task.createdAt === undefined) {
    return false;
  }
  const created = Date.parse(task.createdAt);
  if (Number.isNaN(created)) {
    return false;
  }
  return created <= now && now - created <= TASK_DATE_WINDOW_MS[window];
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
  if (filter.createdWithin !== undefined && !isWithinDateWindow(task, filter.createdWithin, now)) {
    return false;
  }
  const query = normalizeTaskQuery(filter.query).trim().toLocaleLowerCase();
  if (query === "") {
    return true;
  }
  return visibleTaskText(task).toLocaleLowerCase().includes(query);
}

export function filterTasks(tasks: readonly TaskSummary[], filter: TaskInboxFilter): TaskSummary[] {
  // Evaluate every task against one "now" so a window boundary can't shift mid-filter.
  const now = Date.now();
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
    filter.createdWithin !== undefined
  );
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
  if (filter.createdWithin !== undefined) {
    criteria.push(
      `were created in the ${TASK_DATE_WINDOW_LABELS[filter.createdWithin].toLowerCase()}`,
    );
  }
  if (criteria.length === 0) {
    return "No loaded tasks match the current filters.";
  }
  const joined =
    criteria.length === 1
      ? criteria[0]
      : criteria.length === 2
        ? `${criteria[0]} and ${criteria[1]}`
        : `${criteria.slice(0, -1).join(", ")}, and ${criteria[criteria.length - 1]}`;
  return `No loaded tasks ${joined}.`;
}
