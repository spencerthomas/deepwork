export const TASK_STATUSES = Object.freeze([
  "queued",
  "running",
  "needs-review",
  "done",
  "failed",
  "cancelled",
  "status-unavailable",
] as const);

export type TaskStatus = (typeof TASK_STATUSES)[number];

export const VIEW_STATE_KINDS = Object.freeze([
  "loading",
  "empty",
  "success",
  "error",
  "unavailable",
] as const);

export type ViewStateKind = (typeof VIEW_STATE_KINDS)[number];

export function isTaskStatus(value: unknown): value is TaskStatus {
  return (
    typeof value === "string" &&
    (TASK_STATUSES as readonly string[]).includes(value)
  );
}

export function isViewStateKind(value: unknown): value is ViewStateKind {
  return (
    typeof value === "string" &&
    (VIEW_STATE_KINDS as readonly string[]).includes(value)
  );
}
