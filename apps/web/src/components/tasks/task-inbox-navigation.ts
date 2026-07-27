import type { TaskStatusFilter } from "../task-inbox-filter";
import type { TaskStatus, TaskSummary } from "../../lib/task-types";

/**
 * The order status groups render in when the inbox is grouped "by status".
 * Shared by the inbox view and the keyboard navigation so a highlight moving
 * with j/k always visits rows in the exact order they appear on screen.
 */
export const INBOX_GROUP_ORDER: readonly TaskStatus[] = [
  "waiting-approval",
  "running",
  "queued",
  "failed",
  "rejected",
  "cancelled",
  "completed",
  "unknown",
];

/**
 * The task ids in the order the inbox paints them. Grouped-by-status view walks
 * {@link INBOX_GROUP_ORDER} (matching the rendered sections); every other view
 * keeps the already-filtered order. `visible` is expected to be the same list
 * the inbox renders, so navigation and display can never drift.
 */
export function orderedInboxIds(
  visible: readonly TaskSummary[],
  grouped: boolean,
  statusFilter: TaskStatusFilter,
): string[] {
  if (grouped && statusFilter === "all") {
    const ids: string[] = [];
    for (const status of INBOX_GROUP_ORDER) {
      for (const task of visible) {
        if (task.status === status) ids.push(task.taskId);
      }
    }
    return ids;
  }
  return visible.map((task) => task.taskId);
}

function recencyKey(task: TaskSummary): number {
  // Tasks whose creation time is unknown or unparseable sort as the oldest, so
  // they fall to the bottom of a newest-first list rather than masquerading as
  // brand new. Never fabricate a time to fill the gap.
  if (task.createdAt === undefined) {
    return Number.NEGATIVE_INFINITY;
  }
  const parsed = Date.parse(task.createdAt);
  return Number.isNaN(parsed) ? Number.NEGATIVE_INFINITY : parsed;
}

/**
 * The visible tasks ordered newest-created first, so the ungrouped "Recent"
 * view lives up to its name (the API returns tasks oldest-first). The sort is
 * stable, so tasks that share a creation instant — or both lack one — keep
 * their original server order.
 */
export function sortTasksByRecency(tasks: readonly TaskSummary[]): TaskSummary[] {
  return [...tasks].sort((first, second) => {
    const firstKey = recencyKey(first);
    const secondKey = recencyKey(second);
    if (firstKey === secondKey) {
      return 0;
    }
    return secondKey - firstKey;
  });
}

/**
 * The id a j/k / arrow keypress should highlight next. With nothing highlighted
 * yet, moving down lands on the first row and up on the last; otherwise the
 * highlight steps one row and clamps at the ends (no wrap). Returns null only
 * when there is nothing to highlight.
 */
export function moveInboxFocus(
  currentId: string | null,
  ids: readonly string[],
  delta: 1 | -1,
): string | null {
  if (ids.length === 0) return null;
  const index = currentId === null ? -1 : ids.indexOf(currentId);
  if (index === -1) {
    return delta > 0 ? ids[0] : ids[ids.length - 1];
  }
  const next = Math.min(Math.max(index + delta, 0), ids.length - 1);
  return ids[next];
}
