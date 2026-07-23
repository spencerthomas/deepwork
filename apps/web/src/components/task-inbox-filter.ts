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

export interface TaskInboxFilter {
  attentionOnly: boolean;
  query: string;
  status: TaskStatusFilter;
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

export function matchesTaskFilter(task: TaskSummary, filter: TaskInboxFilter): boolean {
  if (filter.status !== "all" && task.status !== filter.status) {
    return false;
  }
  if (filter.attentionOnly && !requiresAttention(task)) {
    return false;
  }
  const query = normalizeTaskQuery(filter.query).trim().toLocaleLowerCase();
  if (query === "") {
    return true;
  }
  return visibleTaskText(task).toLocaleLowerCase().includes(query);
}

export function filterTasks(tasks: readonly TaskSummary[], filter: TaskInboxFilter): TaskSummary[] {
  return tasks.filter((task) => matchesTaskFilter(task, filter));
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
  return filter.query.trim() !== "" || filter.status !== "all" || filter.attentionOnly;
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
  if (criteria.length === 0) {
    return "No loaded tasks match the current filters.";
  }
  const joined =
    criteria.length === 1
      ? criteria[0]
      : criteria.length === 2
        ? `${criteria[0]} and ${criteria[1]}`
        : `${criteria[0]}, ${criteria[1]}, and ${criteria[2]}`;
  return `No loaded tasks ${joined}.`;
}
